import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from medical.lab_marker_dictionary import canonicalize_marker

DATABASE_PATH = ROOT / "database" / "vitalis.db"
PROCESSED_FOLDER = ROOT / "data" / "medical_reports" / "processed"

KNOWN_MARKERS = [
    ("Blood Glucose", "Fasting Blood Sugar"),
    ("Blood Glucose", "Post Prandial Blood Sugar"),
    ("Diabetes", "HbA1c"),
    ("LFT", "SGOT"),
    ("LFT", "SGPT"),
    ("LFT", "AST"),
    ("LFT", "ALT"),
    ("LFT", "GGT"),
    ("LFT", "Bilirubin Total"),
    ("LFT", "Bilirubin Direct"),
    ("LFT", "Bilirubin Indirect"),
    ("LFT", "Alkaline Phosphatase"),
    ("Lipids", "Total Cholesterol"),
    ("Lipids", "LDL"),
    ("Lipids", "HDL"),
    ("Lipids", "Triglycerides"),
    ("CBC", "Hemoglobin"),
    ("CBC", "WBC"),
    ("CBC", "RBC"),
    ("CBC", "Platelet Count"),
    ("Vitamins", "Vitamin D"),
    ("Vitamins", "Vitamin B12"),
    ("Kidney", "Creatinine"),
    ("Kidney", "Urea"),
    ("Kidney", "Uric Acid"),
]


def normalize_space(value):
    return re.sub(r"\s+", " ", value or "").strip()


def parse_report_date(text):
    patterns = [
        r"Reporting Date\s*&?\s*Time\s*:\s*(\d{2}/\d{2}/\d{4})",
        r"Registration Date\s*&?\s*Time\s*:\s*(\d{2}/\d{2}/\d{4})",
        r"Date\s*:\s*(\d{2}/\d{2}/\d{4})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return datetime.strptime(match.group(1), "%d/%m/%Y").date().isoformat()

    return None


def ensure_column(connection, column_name, column_type):
    existing_columns = [
        row[1]
        for row in connection.execute("pragma table_info(medical_lab_results)").fetchall()
    ]

    if column_name not in existing_columns:
        connection.execute(
            f"alter table medical_lab_results add column {column_name} {column_type}"
        )


def create_table(connection):
    connection.execute(
        """
        create table if not exists medical_lab_results (
            id integer primary key autoincrement,
            test_date text not null,
            panel text,
            marker text not null,
            value real,
            unit text,
            reference_low real,
            reference_high real,
            flag text,
            source_file text,
            notes text,
            imported_at text not null,
            unique(test_date, marker, source_file)
        )
        """
    )

    ensure_column(connection, "raw_marker", "text")
    ensure_column(connection, "canonical_marker", "text")
    ensure_column(connection, "category", "text")


def marker_regex(marker):
    escaped = re.escape(marker)
    return re.compile(
        rf"{escaped}\s*:?\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z/%]+)?",
        flags=re.IGNORECASE,
    )


def parse_reference_nearby(text, start_index):
    nearby = text[start_index:start_index + 120]

    range_match = re.search(
        r"([0-9]+(?:\.[0-9]+)?)\s*-\s*([0-9]+(?:\.[0-9]+)?)",
        nearby,
    )

    if range_match:
        return float(range_match.group(1)), float(range_match.group(2))

    upper_match = re.search(
        r"(?:upto|up to|less than|<)\s*([0-9]+(?:\.[0-9]+)?)",
        nearby,
        flags=re.IGNORECASE,
    )

    if upper_match:
        return None, float(upper_match.group(1))

    return None, None


def parse_flag(value, reference_low, reference_high):
    if value is None:
        return None

    if reference_low is not None and value < reference_low:
        return "Low"

    if reference_high is not None and value > reference_high:
        return "High"

    if reference_low is not None or reference_high is not None:
        return "Normal"

    return None


def parse_report_file(text_path):
    text = text_path.read_text(encoding="utf-8", errors="ignore")
    compact_text = normalize_space(text)
    source_file_match = re.search(r"source_file=(.+)", text)

    source_file = (
        source_file_match.group(1).strip()
        if source_file_match
        else text_path.name
    )

    test_date = parse_report_date(compact_text) or "unknown"
    results = []

    for panel, raw_marker in KNOWN_MARKERS:
        pattern = marker_regex(raw_marker)

        for match in pattern.finditer(compact_text):
            value = float(match.group(1))
            unit = match.group(2)
            reference_low, reference_high = parse_reference_nearby(compact_text, match.end())
            canonical_marker, category = canonicalize_marker(raw_marker, panel)
            flag = parse_flag(value, reference_low, reference_high)

            results.append(
                {
                    "test_date": test_date,
                    "panel": panel,
                    "marker": raw_marker,
                    "raw_marker": raw_marker,
                    "canonical_marker": canonical_marker,
                    "category": category,
                    "value": value,
                    "unit": unit,
                    "reference_low": reference_low,
                    "reference_high": reference_high,
                    "flag": flag,
                    "source_file": source_file,
                    "notes": "parsed_from_pdf_text",
                }
            )

    return results


def save_results(rows):
    imported_at = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(DATABASE_PATH) as connection:
        create_table(connection)

        for row in rows:
            connection.execute(
                """
                insert into medical_lab_results (
                    test_date,
                    panel,
                    marker,
                    raw_marker,
                    canonical_marker,
                    category,
                    value,
                    unit,
                    reference_low,
                    reference_high,
                    flag,
                    source_file,
                    notes,
                    imported_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(test_date, marker, source_file)
                do update set
                    panel = excluded.panel,
                    raw_marker = excluded.raw_marker,
                    canonical_marker = excluded.canonical_marker,
                    category = excluded.category,
                    value = excluded.value,
                    unit = excluded.unit,
                    reference_low = excluded.reference_low,
                    reference_high = excluded.reference_high,
                    flag = excluded.flag,
                    notes = excluded.notes,
                    imported_at = excluded.imported_at
                """,
                (
                    row["test_date"],
                    row["panel"],
                    row["marker"],
                    row["raw_marker"],
                    row["canonical_marker"],
                    row["category"],
                    row["value"],
                    row["unit"],
                    row["reference_low"],
                    row["reference_high"],
                    row["flag"],
                    row["source_file"],
                    row["notes"],
                    imported_at,
                ),
            )

        connection.commit()


def main():
    text_files = sorted(PROCESSED_FOLDER.glob("*.txt"))

    if not text_files:
        print(f"No processed text files found in: {PROCESSED_FOLDER}")
        return

    all_rows = []

    for text_path in text_files:
        rows = parse_report_file(text_path)

        if rows:
            print(f"Parsed {len(rows)} lab rows from: {text_path.name}")
            all_rows.extend(rows)

    save_results(all_rows)

    print("Medical report parsing complete.")
    print(f"Imported/updated lab rows: {len(all_rows)}")


if __name__ == "__main__":
    main()