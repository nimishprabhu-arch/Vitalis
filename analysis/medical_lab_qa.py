import csv
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "database" / "vitalis.db"
PROCESSED_DIR = ROOT / "data" / "medical_reports" / "processed"
REVIEW_PATH = ROOT / "data" / "medical_reports" / "needs_review.csv"


EXPECTED_MARKERS = {
    "CBC": {
        "hemoglobin": "Hemoglobin",
        "haemoglobin": "Hemoglobin",
        "hematocrit": "Hematocrit",
        "hct": "Hematocrit",
        "pcv": "Hematocrit",
        "rbc": "RBC",
        "rbc count": "RBC",
        "wbc": "WBC",
        "total wbc": "WBC",
        "total wbc count": "WBC",
        "platelet": "Platelet Count",
        "platelets": "Platelet Count",
        "platelets count": "Platelet Count",
        "mcv": "MCV",
        "mch": "MCH",
        "mchc": "MCHC",
        "rdw": "RDW",
    },
    "Glucose": {
        "fasting blood sugar": "Fasting Blood Sugar",
        "post prandial blood sugar": "Post Prandial Blood Sugar",
        "hba1c": "HbA1c",
        "glycosylated": "HbA1c",
        "estimated average glucose": "Estimated Average Glucose",
    },
    "Lipids": {
        "cholesterol": "Total Cholesterol",
        "total cholesterol": "Total Cholesterol",
        "triglyceride": "Triglycerides",
        "triglycerides": "Triglycerides",
        "hdl": "HDL",
        "hdl - cholesterol": "HDL",
        "ldl": "LDL",
        "ldl - cholesterol": "LDL",
        "vldl": "VLDL",
        "cholesterol/hdl ratio": "Cholesterol/HDL Ratio",
        "ldl / hdl ratio": "LDL/HDL Ratio",
    },
    "Kidney": {
        "creatinine": "Creatinine",
        "urea": "Urea",
        "bun": "BUN",
        "uric acid": "Uric Acid",
    },
    "Liver": {
        "bilirubin": "Bilirubin",
        "alkaline phosphatase": "Alkaline Phosphatase",
        "ast": "AST",
        "sgot": "AST",
        "alt": "ALT",
        "sgpt": "ALT",
        "ggt": "GGT",
    },
    "Thyroid": {
        "thyroid": "Thyroid Panel",
        "free t3": "Free T3",
        "t3": "Free T3",
        "free t4": "Free T4",
        "t4": "Free T4",
        "tsh": "TSH",
    },
    "Infectious Disease": {
        "hbsag": "HBsAg",
        "australia antigen": "HBsAg",
        "hiv": "HIV",
        "hcv": "HCV",
        "hepatitis c": "HCV",
    },
    "Pancreas": {
        "amylase": "Amylase",
        "lipase": "Lipase",
    },
    "Vitamins": {
        "vitamin d": "Vitamin D",
        "vitamin b12": "Vitamin B12",
    },
    "Urine": {
        "urine sugar": "Urine Sugar",
        "urine acetone": "Urine Ketones",
        "urine ketone": "Urine Ketones",
        "urine ketones": "Urine Ketones",
    },
}


SUSPICIOUS_UNIT_PATTERN = re.compile(r"[a-zA-Z/%µ]+(?:\d|\.)")
GLUED_RESULT_PATTERN = re.compile(r"\d+\s*[a-zA-Z/%µ]+\d+")

ZERO_SHOULD_REVIEW = {
    "Hemoglobin",
    "Hematocrit",
    "RBC",
    "WBC",
    "Platelet Count",
    "MCV",
    "MCH",
    "MCHC",
    "RDW",
    "Creatinine",
    "Urea",
    "BUN",
    "Uric Acid",
    "Total Cholesterol",
    "HDL",
    "LDL",
    "Triglycerides",
    "HbA1c",
}


def normalize_text(value):
    return re.sub(r"\s+", " ", value.lower()).strip()


def load_db_rows():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            select
                test_date,
                category,
                canonical_marker,
                marker,
                value,
                result_text,
                unit,
                reference_low,
                reference_high,
                flag,
                source_file
            from medical_lab_results
            """
        ).fetchall()

    by_source = defaultdict(list)
    by_marker = defaultdict(list)

    for row in rows:
        by_source[row["source_file"]].append(row)
        by_marker[row["canonical_marker"]].append(row)

    return rows, by_source, by_marker


def detect_expected_markers(text):
    normalized = normalize_text(text)
    normalized_for_cbc = normalized.replace("glycosylated haemoglobin", "")
    normalized_for_cbc = normalized_for_cbc.replace("glycosylated hemoglobin", "")
    found = []

    for category, aliases in EXPECTED_MARKERS.items():
        for alias, canonical_marker in aliases.items():
            alias_normalized = alias.lower()
            alias_pattern = re.escape(alias_normalized)

            search_text = normalized_for_cbc if category == "CBC" else normalized

            if len(alias_normalized) <= 4:
                pattern = rf"(?<![a-z0-9]){alias_pattern}(?![a-z0-9])"
                matched = re.search(pattern, search_text) is not None
            else:
                matched = alias_normalized in search_text

            if matched:
                found.append((category, canonical_marker, alias))

    seen = set()
    unique_found = []

    for item in found:
        key = (item[0], item[1])
        if key not in seen:
            seen.add(key)
            unique_found.append(item)

    return unique_found


def source_candidates_for_text_file(path):
    return {
        path.name,
        path.with_suffix(".pdf").name,
        path.stem + ".pdf",
    }


def has_db_marker(rows, canonical_marker):
    return any(row["canonical_marker"] == canonical_marker for row in rows)


def format_row_result(row):
    value = row["value"]
    result_text = row["result_text"]
    unit = row["unit"]

    if value is not None:
        return f"{value:g} {unit or ''}".strip()

    if result_text:
        return result_text

    return "EMPTY"


def review_item(issue_type, severity, source_file, marker="", category="", detail="", suggested_action=""):
    return {
        "issue_type": issue_type,
        "severity": severity,
        "source_file": source_file or "",
        "category": category or "",
        "marker": marker or "",
        "detail": detail or "",
        "suggested_action": suggested_action or "",
    }


def print_section(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def collect_coverage_reviews(by_source):
    reviews = []
    text_files = sorted(PROCESSED_DIR.glob("*.txt"))

    for path in text_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        expected = detect_expected_markers(text)

        source_rows = []
        for candidate in source_candidates_for_text_file(path):
            source_rows.extend(by_source.get(candidate, []))

        if expected and not source_rows:
            labels = sorted({f"{category}: {marker}" for category, marker, _ in expected})
            reviews.append(
                review_item(
                    "report_has_expected_markers_but_no_db_rows",
                    "high",
                    path.with_suffix(".pdf").name,
                    detail=", ".join(labels),
                    suggested_action="Check parser coverage for this PDF format.",
                )
            )
            continue

        for category, canonical_marker, alias in expected:
            if not has_db_marker(source_rows, canonical_marker):
                reviews.append(
                    review_item(
                        "expected_marker_missing_from_db",
                        "medium",
                        path.with_suffix(".pdf").name,
                        marker=canonical_marker,
                        category=category,
                        detail=f"Detected text alias: {alias}",
                        suggested_action="Add alias or layout handling to parser if this marker should be imported.",
                    )
                )

    return reviews


def collect_suspicious_row_reviews(rows):
    reviews = []
    seen_exact_rows = set()

    for row in rows:
        result = format_row_result(row)
        unit = row["unit"] or ""
        marker = row["canonical_marker"] or row["marker"] or ""
        source_file = row["source_file"] or ""

        exact_key = (
            row["test_date"],
            marker,
            row["value"],
            row["result_text"],
            unit,
            source_file,
        )

        if exact_key in seen_exact_rows:
            reviews.append(
                review_item(
                    "duplicate_lab_row",
                    "low",
                    source_file,
                    marker=marker,
                    category=row["category"],
                    detail=f"Duplicate row: {result}",
                    suggested_action="Usually safe, but check if duplicate PDFs are present.",
                )
            )
        else:
            seen_exact_rows.add(exact_key)

        if row["test_date"] in {None, "", "unknown"}:
            reviews.append(
                review_item(
                    "unknown_test_date",
                    "high",
                    source_file,
                    marker=marker,
                    category=row["category"],
                    detail=f"Result: {result}",
                    suggested_action="Fix date extraction or skip this row from cloud upload.",
                )
            )

        if row["value"] is None and not row["result_text"]:
            reviews.append(
                review_item(
                    "empty_result",
                    "medium",
                    source_file,
                    marker=marker,
                    category=row["category"],
                    detail="No numeric value or text result was parsed.",
                    suggested_action="Verify against source PDF.",
                )
            )

        if row["value"] == 0 and marker in ZERO_SHOULD_REVIEW:
            reviews.append(
                review_item(
                    "suspicious_zero_value",
                    "high",
                    source_file,
                    marker=marker,
                    category=row["category"],
                    detail=f"Parsed value is 0 for marker where zero is unlikely.",
                    suggested_action="Check whether parser captured chart axis or placeholder text.",
                )
            )

        if unit and SUSPICIOUS_UNIT_PATTERN.search(unit):
            reviews.append(
                review_item(
                    "suspicious_unit_text",
                    "medium",
                    source_file,
                    marker=marker,
                    category=row["category"],
                    detail=f"Unit looks glued or contaminated: {unit}",
                    suggested_action="Check parser unit pattern.",
                )
            )

        if GLUED_RESULT_PATTERN.search(result):
            reviews.append(
                review_item(
                    "glued_result_text",
                    "medium",
                    source_file,
                    marker=marker,
                    category=row["category"],
                    detail=f"Result may contain glued unit/reference: {result}",
                    suggested_action="Check value/unit/reference extraction.",
                )
            )

    return reviews


def write_needs_review(reviews):
    REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "issue_type",
        "severity",
        "source_file",
        "category",
        "marker",
        "detail",
        "suggested_action",
    ]

    with REVIEW_PATH.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reviews)


def report_db_summary(rows):
    print_section("DB Summary")
    print(f"Total lab rows: {len(rows)}")

    by_category = defaultdict(int)
    by_marker = defaultdict(int)

    for row in rows:
        by_category[row["category"] or "Uncategorized"] += 1
        by_marker[row["canonical_marker"] or "Uncategorized"] += 1

    print()
    print("Rows by category:")
    for category, count in sorted(by_category.items(), key=lambda item: (-item[1], item[0])):
        print(f"- {category}: {count}")

    print()
    print("Rows by marker:")
    for marker, count in sorted(by_marker.items(), key=lambda item: item[0]):
        print(f"- {marker}: {count}")


def report_reviews(reviews):
    print_section("Needs Review")

    if not reviews:
        print("Needs review rows: 0")
        print(f"Review file written: {REVIEW_PATH}")
        return

    counts = defaultdict(int)
    for item in reviews:
        counts[(item["severity"], item["issue_type"])] += 1

    print(f"Needs review rows: {len(reviews)}")
    print(f"Review file written: {REVIEW_PATH}")
    print()
    print("Review summary:")
    for (severity, issue_type), count in sorted(counts.items()):
        print(f"- {severity} | {issue_type}: {count}")

    print()
    print("Top review items:")
    for item in reviews[:30]:
        print(
            f"- {item['severity']} | {item['issue_type']} | "
            f"{item['source_file']} | {item['marker']} | {item['detail']}"
        )


def report_latest_real_values(by_marker):
    print_section("Latest Real Values")

    for marker in sorted(by_marker):
        real_rows = [
            row for row in by_marker[marker]
            if row["value"] is not None or row["result_text"]
        ]

        if not real_rows:
            continue

        latest = sorted(real_rows, key=lambda row: row["test_date"], reverse=True)[0]
        print(
            f"- {marker}: {format_row_result(latest)} | "
            f"date={latest['test_date']} | category={latest['category']} | "
            f"flag={latest['flag'] or '-'} | source={latest['source_file']}"
        )


def main():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    if not PROCESSED_DIR.exists():
        raise FileNotFoundError(f"Processed report folder not found: {PROCESSED_DIR}")

    rows, by_source, by_marker = load_db_rows()

    coverage_reviews = collect_coverage_reviews(by_source)
    suspicious_reviews = collect_suspicious_row_reviews(rows)
    reviews = coverage_reviews + suspicious_reviews

    write_needs_review(reviews)

    print("Vitalis Medical Lab QA")
    print("-" * 72)

    report_db_summary(rows)
    report_reviews(reviews)
    report_latest_real_values(by_marker)

    print()
    print("QA complete.")


if __name__ == "__main__":
    main()
