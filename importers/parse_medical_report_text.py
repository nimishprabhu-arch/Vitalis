import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from medical.lab_marker_dictionary import canonicalize_marker

DATABASE_PATH = ROOT / "database" / "vitalis.db"
PROCESSED_REPORTS_DIR = ROOT / "data" / "medical_reports" / "processed"

KNOWN_MARKERS = [
    ("Glucose", "Fasting Blood Sugar"),
    ("Glucose", "Post Prandial Blood Sugar"),
    ("Glucose", "HbA1c"),
    ("Glucose", "Estimated Average Glucose"),

    ("Lipids", "Total Cholesterol"),
    ("Lipids", "HDL"),
    ("Lipids", "LDL"),
    ("Lipids", "Triglycerides"),
    ("Lipids", "VLDL"),
    ("Lipids", "Cholesterol/HDL Ratio"),
    ("Lipids", "LDL/HDL Ratio"),

    ("CBC", "Hemoglobin"),
    ("CBC", "RBC"),
    ("CBC", "Hematocrit"),
    ("CBC", "MCV"),
    ("CBC", "MCH"),
    ("CBC", "MCHC"),
    ("CBC", "RDW"),
    ("CBC", "WBC"),
    ("CBC", "Platelet Count"),

    ("Kidney", "Creatinine"),
    ("Kidney", "Urea"),
    ("Kidney", "Uric Acid"),
    ("Kidney", "BUN"),

    ("Liver", "ALT"),
    ("Liver", "AST"),
    ("Liver", "GGT"),
    ("Liver", "Alkaline Phosphatase"),
    ("Liver", "Bilirubin"),

    ("Pancreas", "Amylase"),
    ("Pancreas", "Lipase"),

    ("Thyroid", "Free T3"),
    ("Thyroid", "Free T4"),
    ("Thyroid", "TSH"),

    ("Vitamins", "Vitamin D"),
    ("Vitamins", "Vitamin B12"),
]

QUALITATIVE_MARKERS = [
    ("Infectious Disease", "HBsAg"),
    ("Infectious Disease", "HIV"),
    ("Infectious Disease", "HCV"),
    ("Urine", "Fasting Urine Sugar"),
    ("Urine", "Post Prandial Urine Sugar"),
    ("Urine", "Fasting Urine Aceton"),
    ("Urine", "Post Prandial Urine Acetone"),
]

DATE_PATTERNS = [
    re.compile(r"Registration Date\s*&\s*Time:\s*(\d{2}/\d{2}/\d{4})", re.IGNORECASE),
    re.compile(r"Reporting Date\s*&\s*Time:\s*(\d{2}/\d{2}/\d{4})", re.IGNORECASE),
    re.compile(r"(\d{2}/\d{2}/\d{4})"),
    re.compile(r"Sample Collection Date\s*:\s*(\d{2}/[A-Za-z]{3}/\d{4})", re.IGNORECASE),
]


def clean_text(value):
    value = (value or "").strip()

    if not value:
        return None

    replacements = {
        "mg/dLDesirable": "mg/dL",
        "mg/dLOptimal": "mg/dL",
        "mg/dLFavourable": "mg/dL",
        "mg/dLNormal": "mg/dL",
        "mg/dlDesirable": "mg/dl",
        "mg/dlOptimal": "mg/dl",
        "mg/dlFavourable": "mg/dl",
        "mg/dlNormal": "mg/dl",
        "%NormaL": "%",
        "%Normal": "%",
        "Eythyroid": "",
        "Euthyroid": "",
        "up": "",
        "LDL": "",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = value.strip()
    return value if value else None


def parse_report_date(text):
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            raw_date = match.group(1)
            try:
                date_format = "%d/%b/%Y" if re.search(r"/[A-Za-z]{3}/", raw_date) else "%d/%m/%Y"
                return datetime.strptime(raw_date, date_format).date().isoformat()
            except ValueError:
                continue

    return None


def parse_float(value):
    value = clean_text(value)
    if not value:
        return None

    value = value.replace(",", "")
    try:
        return float(value)
    except ValueError:
        return None


def marker_regex(marker):
    marker_patterns = {
        "Fasting Blood Sugar": r"Fasting\s+Blood\s+Sugar",
        "Post Prandial Blood Sugar": r"Post\s+Prandial\s+Blood\s+Sugar",
        "HbA1c": r"(?:Glycosylated\s+HB\s*\(\s*HbA1C\s*\)|HbA1C|Glycosylated\s+Haemoglobin|Glycosylated\s+Hemoglobin)",
        "Estimated Average Glucose": r"Estimated\s+Average\s+Glucose",

        "Total Cholesterol": r"(?<!HDL - )(?<!LDL - )\bCholesterol\b",
        "Triglycerides": r"Triglycerides?",
        "HDL": r"HDL\s*-?\s*Cholesterol",
        "LDL": r"LDL\s*-?\s*Cholesterol",
        "VLDL": r"\bVLDL\b",
        "Cholesterol/HDL Ratio": r"Cholesterol\s*/\s*HDL\s+Ratio",
        "LDL/HDL Ratio": r"LDL\s*/\s*HDL\s+Ratio",

        "Hemoglobin": r"(?:Haemoglobin|Hemoglobin|Hb)",
        "WBC": r"(?:Total\s+WBC\s+Count|WBC\s+Count|WBC|White\s+Blood\s+Cells|Total\s+Leu[ck]ocyte\s+Count|TLC)",
        "RBC": r"(?:RBC\s+Count|RBC|Red\s+Blood\s+Cells|Red\s+Blood\s+Cell\s+Count)",
        "Platelet Count": r"(?:Platelets\s+Count|Platelet\s+Count|Platelets|Platelet)",
        "Hematocrit": r"(?:HCT|Haematocrit|Hematocrit|PCV)",
        "MCV": r"\bMCV\b",
        "MCH": r"\bMCH\b",
        "MCHC": r"\bMCHC\b",
        "RDW": r"\bRDW\b",

        "Creatinine": r"(?:Serum\s+)?Creatinine",
        "Urea": r"(?:Blood\s+)?Urea",
        "Uric Acid": r"Uric\s+Acid",
        "BUN": r"(?:Blood\s+Urea\s+Nitrogen|BUN)",

        "AST": r"(?:AST|SGOT)",
        "ALT": r"(?:ALT|SGPT)",
        "GGT": r"(?:GGTP|GGT|Gamma\s*GT|Gamma\s+Glutamyl\s+Transferase)",
        "Alkaline Phosphatase": r"(?:Alkaline\s+Phosphatase|ALP)",
        "Bilirubin": r"(?:Total\s+)?Bilirubin",

        "Amylase": r"\bAmylase\b",
        "Lipase": r"\bLipase\b",

        "Free T3": r"Free\s+T3\s*\(\s*Free\s+Triiodothyronine\s*\)",
        "Free T4": r"Free\s+T4\s*\(\s*Free\s+Thyroxine\s*\)",
        "TSH": r"TSH\s*\(\s*ULTRASENSITIVE\s*\)",

        "Vitamin D": r"(?:Vitamin\s+D|25\s*-?\s*Hydroxy\s+Vitamin\s+D|25\s*-?\s*OH\s+Vitamin\s+D)",
        "Vitamin B12": r"(?:Vitamin\s+B12|B12)",
    }

    marker_pattern = marker_patterns.get(marker, re.escape(marker))
    unit_pattern = r"(mg/dL|mg/dl|g/dl|M/uL|/cumm|mmol/L|uIU/ml|pg/ml|ng/dl|U/L|fL|fl|pg|%)"

    return re.compile(
        rf"{marker_pattern}\s*:?\s*([<>]?\s*\d+(?:\.\d+)?)\s*({unit_pattern})?",
        flags=re.IGNORECASE,
    )
    marker_pattern = marker_patterns.get(marker, re.escape(marker))

    return re.compile(
        rf"{marker_pattern}\s*:?\s*([<>]?\s*\d+(?:\.\d+)?)\s*([a-zA-Z0-9/%Âµ\.]+)?",
        flags=re.IGNORECASE,
    )


def marker_regex(marker):
    marker_pattern = re.escape(marker).replace(r"\ ", r"\s+")

    method_words = (
        r"(?:Spectrophotometric|Elect\.\s*Impedance|Calculated|Measured|"
        r"Photometry|Impedance|Colorimetric|Enzymatic|CLIA|ECLIA)"
    )

    unit_pattern = (
        r"(?:mg/dL|mg/dl|g/dL|g/dl|mil/cmm|M/uL|/cmm|/cumm|"
        r"mmol/L|uIU/ml|pg/ml|ng/dl|U/L|fL|fl|pg|%)"
    )

    return re.compile(
        rf"(?<![A-Za-z]){marker_pattern}\s+"
        rf"([<>]?\s*\d[\d,]*(?:\.\d+)?)"
        rf"(?:\s+{method_words})?"
        rf"\s*(\d[\d,]*(?:\.\d+)?)?\s*-\s*(\d[\d,]*(?:\.\d+)?)?"
        rf"\s*({unit_pattern})?",
        flags=re.IGNORECASE,
    )


def normalize_result_text(value):
    value = clean_text(value)

    if not value:
        return None

    normalized = value.upper().replace(" ", "-")

    if normalized in {"NON-REACTIVE", "NONREACTIVE"}:
        return "Non-reactive"

    if normalized == "NEGATIVE":
        return "Negative"

    if normalized == "POSITIVE":
        return "Positive"

    if normalized == "REACTIVE":
        return "Reactive"

    return value


def find_reference_range(text, start_index):
    nearby_text = text[start_index : start_index + 140]
    match = re.search(r"(\d+(?:\.\d+)?)\s*[-â€“]\s*(\d+(?:\.\d+)?)", nearby_text)

    if not match:
        return None, None

    return parse_float(match.group(1)), parse_float(match.group(2))


def calculate_flag(value, reference_low, reference_high):
    if value is None:
        return None

    if reference_low is not None and value < reference_low:
        return "low"

    if reference_high is not None and value > reference_high:
        return "high"

    return "normal"


def create_table(connection):
    connection.execute(
        """
        create table if not exists medical_lab_results (
            id integer primary key autoincrement,
            test_date text not null,
            panel text,
            marker text not null,
            value real,
            result_text text,
            unit text,
            reference_low real,
            reference_high real,
            flag text,
            source_file text,
            notes text,
            imported_at text not null,
            raw_marker text,
            canonical_marker text,
            category text,
            unique(test_date, marker, source_file)
        )
        """
    )

    ensure_column(connection, "result_text", "text")
    ensure_column(connection, "raw_marker", "text")
    ensure_column(connection, "canonical_marker", "text")
    ensure_column(connection, "category", "text")


def ensure_column(connection, column_name, column_type):
    columns = [row[1] for row in connection.execute("pragma table_info(medical_lab_results)")]

    if column_name not in columns:
        connection.execute(f"alter table medical_lab_results add column {column_name} {column_type}")

def qualitative_marker_regex(marker):
    marker_pattern = re.escape(marker).replace(r"\ ", r"\s+")

    qualitative_values = (
        r"(Negative|NEGATIVE|Non[\s-]?Reactive|NON[\s-]?REACTIVE|"
        r"Reactive|REACTIVE|Positive|POSITIVE|Absent|ABSENT|"
        r"Present|PRESENT|No\s+Sample|NO\s+SAMPLE)"
    )

    return re.compile(
        rf"{marker_pattern}\s*:?\s*{qualitative_values}",
        flags=re.IGNORECASE,
    )

def parse_report_file(path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    compact_text = re.sub(r"\s+", " ", text)
    test_date = parse_report_date(compact_text)

    if not test_date:
        return []

    source_file = path.name.replace(".txt", ".pdf")
    results = []

    for panel, raw_marker in KNOWN_MARKERS:
        pattern = marker_regex(raw_marker)

        for match in pattern.finditer(compact_text):
            value = parse_float(match.group(1))
            reference_low = parse_float(match.group(2)) if match.lastindex and match.lastindex >= 2 else None
            reference_high = parse_float(match.group(3)) if match.lastindex and match.lastindex >= 3 else None
            unit = clean_text(match.group(4)) if match.lastindex and match.lastindex >= 4 else None

            if reference_low is None or reference_high is None:
                fallback_low, fallback_high = find_reference_range(compact_text, match.end())
                reference_low = reference_low if reference_low is not None else fallback_low
                reference_high = reference_high if reference_high is not None else fallback_high

            flag = calculate_flag(value, reference_low, reference_high)
            canonical_marker, category = canonicalize_marker(raw_marker, panel)

            results.append(
                {
                    "test_date": test_date,
                    "panel": panel,
                    "marker": raw_marker,
                    "raw_marker": raw_marker,
                    "canonical_marker": canonical_marker,
                    "category": category,
                    "value": value,
                    "result_text": None,
                    "unit": unit,
                    "reference_low": reference_low,
                    "reference_high": reference_high,
                    "flag": flag,
                    "source_file": source_file,
                    "notes": "parsed_from_pdf_text",
                }
            )
    for panel, raw_marker in QUALITATIVE_MARKERS:
        pattern = qualitative_marker_regex(raw_marker)

        for match in pattern.finditer(compact_text):
            result_text = normalize_result_text(match.group(1))
            canonical_marker, category = canonicalize_marker(raw_marker, panel)

            results.append(
                {
                    "test_date": test_date,
                    "panel": panel,
                    "marker": raw_marker,
                    "raw_marker": raw_marker,
                    "canonical_marker": canonical_marker,
                    "category": category,
                    "value": None,
                    "result_text": result_text,
                    "unit": None,
                    "reference_low": None,
                    "reference_high": None,
                    "flag": result_text,
                    "source_file": source_file,
                    "notes": "parsed_from_pdf_text",
                }
            )


    special_patterns = [
        (
            "CBC",
            "WBC Total Count",
            r"WBC\s+Total\s+Count\s+([\d,]+)\s+Elect\.\s*Impedance\s*([\d,]+)\s*-\s*([\d,]+)\s*(/cmm|/cumm)?",
        ),
        (
            "Kidney",
            "URIC ACID, Serum",
            r"([\d.]+)\s*-\s*([\d.]+)\s*(mg/dL|mg/dl)\s+Uricase\s*([\d.]+)\s*URIC\s+ACID,\s*Serum",
        ),
    ]

    for panel, raw_marker, pattern_text in special_patterns:
        pattern = re.compile(pattern_text, flags=re.IGNORECASE)

        for match in pattern.finditer(compact_text):
            if raw_marker == "URIC ACID, Serum":
                reference_low = parse_float(match.group(1))
                reference_high = parse_float(match.group(2))
                unit = clean_text(match.group(3))
                value = parse_float(match.group(4))
            else:
                value = parse_float(match.group(1))
                reference_low = parse_float(match.group(2))
                reference_high = parse_float(match.group(3))
                unit = clean_text(match.group(4))

            flag = calculate_flag(value, reference_low, reference_high)
            canonical_marker, category = canonicalize_marker(raw_marker, panel)

            results.append(
                {
                    "test_date": test_date,
                    "panel": panel,
                    "marker": raw_marker,
                    "raw_marker": raw_marker,
                    "canonical_marker": canonical_marker,
                    "category": category,
                    "value": value,
                    "result_text": None,
                    "unit": unit,
                    "reference_low": reference_low,
                    "reference_high": reference_high,
                    "flag": flag,
                    "source_file": source_file,
                    "notes": "parsed_from_pdf_text_special_layout",
                }
            )


    special_layout_patterns = [
        (
            "CBC",
            "Haemoglobin",
            "Hemoglobin",
            r"Haemoglobin\s+([\d.]+)\s+Spectrophotometric\s*([\d.]+)\s*-\s*([\d.]+)\s*(g/dL|g/dl)",
        ),
        (
            "CBC",
            "WBC Total Count",
            "WBC",
            r"WBC\s+Total\s+Count\s+([\d,]+)\s+Elect\.\s*Impedance\s*([\d,]+)\s*-\s*([\d,]+)\s*(/cmm|/cumm)",
        ),
        
        
                (
            "Vitamins",
            "Vitamin B12",
            "Vitamin B12",
            r"VITAMIN\s+B12\s+Method:\s*CLIA.*?([\d.]+)\s*(pg/ml|pg/mL)\s*([\d.]+)\s*[–-]\s*([\d.]+)",
        ),
        (
            "Vitamins",
            "Vitamin D",
            "Vitamin D",
            r"VITAMIN\s+D\s*\(25\s*-\s*OH\s*VITAMIN\s*D\)\s+Method:\s*CLIA.*?([\d.]+)\s*(ng/ml|ng/mL)\s*([\d.]+)\s*[–-]\s*([\d.]+)",
        ),
        
        (
            "CBC",
            "Platelet Count",
            "Platelet Count",
            r"Platelet\s+Count\s+([\d,]+)\s+Elect\.\s*Impedance\s*([\d,]+)\s*-\s*([\d,]+)\s*(/cmm|/cumm)",
        ),
        (
            "Kidney",
            "URIC ACID, Serum",
            "Uric Acid",
            r"([\d.]+)\s*-\s*([\d.]+)\s*(mg/dL|mg/dl)\s+Uricase\s*([\d.]+)\s*URIC\s+ACID,\s*Serum",
        ),
        (
            "Kidney",
            "Blood Urea Nitrogen",
            "BUN",
            r"Blood\s+Urea\s+Nitrogen\s*:?\s*([\d.]+)\s*(mg/dL|mg/dl)\s*([\d.]+)\s*-\s*([\d.]+)\s*(mg/dL|mg/dl)",
        ),
        (
            "Pancreas",
            "Amylase",
            "Amylase",
            r"Amylase\s*:?\s*([\d.]+)\s*(U/L)\s*([\d.]+)\s*-\s*([\d.]+)\s*(U/L)",
        ),
    ]

    for panel, raw_marker, canonical_hint, pattern_text in special_layout_patterns:
        pattern = re.compile(pattern_text, flags=re.IGNORECASE)

        for match in pattern.finditer(compact_text):
            if canonical_hint == "Uric Acid":
                reference_low = parse_float(match.group(1))
                reference_high = parse_float(match.group(2))
                unit = clean_text(match.group(3))
                value = parse_float(match.group(4))
            elif canonical_hint in {"BUN", "Amylase", "Vitamin B12", "Vitamin D"}:
                value = parse_float(match.group(1))
                unit = clean_text(match.group(2))
                reference_low = parse_float(match.group(3))
                reference_high = parse_float(match.group(4))
            else:
                value = parse_float(match.group(1))
                reference_low = parse_float(match.group(2))
                reference_high = parse_float(match.group(3))
                unit = clean_text(match.group(4))

            flag = calculate_flag(value, reference_low, reference_high)
            canonical_marker, category = canonicalize_marker(raw_marker, panel)

            results = [
                row
                for row in results
                if not (
                    row["source_file"] == source_file
                    and row["test_date"] == test_date
                    and row["canonical_marker"] == canonical_marker
                    and row.get("value") == 0
                )
            ]

            results.append(
                {
                    "test_date": test_date,
                    "panel": panel,
                    "marker": raw_marker,
                    "raw_marker": raw_marker,
                    "canonical_marker": canonical_marker,
                    "category": category,
                    "value": value,
                    "result_text": None,
                    "unit": unit,
                    "reference_low": reference_low,
                    "reference_high": reference_high,
                    "flag": flag,
                    "source_file": source_file,
                    "notes": "parsed_from_pdf_text_special_layout",
                }
            )

    lipid_layout_patterns = [
        (
            "Total Cholesterol",
            "Total Cholesterol",
            r"LIPID\s+PROFILE.*?Test\s+Result\s+Unit\s+Normal\s+Range\s+Cholesterol\s*:?\s*([\d.]+)\s*(mg/dL|mg/dl).*?Boderline\s+High\s*([\d.]+)\s*-\s*([\d.]+)",
        ),
        (
            "Triglycerides",
            "Triglycerides",
            r"Triglyceride\s*:?\s*([\d.]+)\s*(mg/dL|mg/dl).*?Boderline\s+High\s*([\d.]+)\s*-\s*([\d.]+)",
        ),
        (
            "HDL",
            "HDL",
            r"HDL\s*-\s*Cholesterol\s*:?\s*([\d.]+)\s*(mg/dL|mg/dl).*?Standard\s+risk\s*([\d.]+)\s*-\s*([\d.]+)",
        ),
        (
            "LDL",
            "LDL",
            r"LDL\s*-\s*Cholesterol\s*:?\s*([\d.]+)\s*(mg/dL|mg/dl).*?Boderline\s+high\s*([\d.]+)\s*-\s*([\d.]+)",
        ),
        (
            "VLDL",
            "VLDL",
            r"\bVLDL\s*:?\s*([\d.]+)\s*(mg/dL|mg/dl)\s*([\d.]+)\s*-\s*([\d.]+)",
        ),
        (
            "Cholesterol/HDL Ratio",
            "Cholesterol/HDL Ratio",
            r"Cholesterol\s*/\s*HDL\s+Ratio\s*:?\s*([\d.]+)",
        ),
        (
            "LDL/HDL Ratio",
            "LDL/HDL Ratio",
            r"LDL\s*/\s*HDL\s+Ratio\s*:?\s*([\d.]+)",
        ),
    ]

    lipid_rows = []

    for raw_marker, canonical_marker in [
        ("Total Cholesterol", "Total Cholesterol"),
        ("Triglycerides", "Triglycerides"),
        ("HDL", "HDL"),
        ("LDL", "LDL"),
        ("VLDL", "VLDL"),
        ("Cholesterol/HDL Ratio", "Cholesterol/HDL Ratio"),
        ("LDL/HDL Ratio", "LDL/HDL Ratio"),
    ]:
        pattern_text = next(
            pattern for marker_name, _, pattern in lipid_layout_patterns if marker_name == raw_marker
        )
        pattern = re.compile(pattern_text, flags=re.IGNORECASE)

        for match in pattern.finditer(compact_text):
            value = parse_float(match.group(1))
            unit = clean_text(match.group(2)) if match.lastindex and match.lastindex >= 2 else None
            reference_low = parse_float(match.group(3)) if match.lastindex and match.lastindex >= 3 else None
            reference_high = parse_float(match.group(4)) if match.lastindex and match.lastindex >= 4 else None

            if canonical_marker == "LDL":
                reference_low = 100.0
                reference_high = 129.0
            elif canonical_marker == "Total Cholesterol":
                reference_low = 200.0
                reference_high = 239.0
            elif canonical_marker == "Triglycerides":
                reference_low = 150.0
                reference_high = 199.0
            elif canonical_marker == "HDL":
                reference_low = 35.0
                reference_high = 55.0

            flag = calculate_flag(value, reference_low, reference_high)
            canonicalized_marker, category = canonicalize_marker(canonical_marker, "Lipids")

            lipid_rows.append(
                {
                    "test_date": test_date,
                    "panel": "Lipids",
                    "marker": raw_marker,
                    "raw_marker": raw_marker,
                    "canonical_marker": canonicalized_marker,
                    "category": category,
                    "value": value,
                    "result_text": None,
                    "unit": unit,
                    "reference_low": reference_low,
                    "reference_high": reference_high,
                    "flag": flag,
                    "source_file": source_file,
                    "notes": "parsed_from_pdf_text_lipid_layout",
                }
            )

    if lipid_rows:
        lipid_markers = {row["canonical_marker"] for row in lipid_rows}

        results = [
            row
            for row in results
            if not (
                row["source_file"] == source_file
                and row["test_date"] == test_date
                and row["canonical_marker"] in lipid_markers
            )
        ]

        results.extend(lipid_rows)


    value_before_patterns = [
        ("CBC", "Haemoglobin", "Hemoglobin", r"([\d.]+)\s*Haemoglobin\s+Spectrophotometric\s*([\d.]+)\s*-\s*([\d.]+)\s*(g/dL|g/dl)"),
        ("CBC", "RBC", "RBC", r"([\d.]+)\s*RBC\s+Elect\.\s*Impedance\s*([\d.]+)\s*-\s*([\d.]+)\s*(mil/cmm)"),
        ("CBC", "PCV", "Hematocrit", r"([\d.]+)\s*PCV\s+Calculated\s*([\d.]+)\s*-\s*([\d.]+)\s*(%)"),
        ("CBC", "MCV", "MCV", r"([\d.]+)\s*MCV\s+Measured\s*([\d.]+)\s*-\s*([\d.]+)\s*(fL|fl)"),
        ("CBC", "MCH", "MCH", r"([\d.]+)\s*MCH\s+Calculated\s*([\d.]+)\s*-\s*([\d.]+)\s*(pg)"),
        ("CBC", "MCHC", "MCHC", r"([\d.]+)\s*MCHC\s+Calculated\s*([\d.]+)\s*-\s*([\d.]+)\s*(g/dL|g/dl)"),
        ("CBC", "RDW", "RDW", r"([\d.]+)\s*RDW\s+Calculated\s*([\d.]+)\s*-\s*([\d.]+)\s*(%)"),
        ("CBC", "PCV", "Hematocrit", r"PCV\s+([\d.]+)\s+Calculated\s*([\d.]+)\s*-\s*([\d.]+)\s*(%)"),
        ("CBC", "WBC Total Count", "WBC", r"([\d,]+)\s*WBC\s+Total\s+Count\s+Elect\.\s*Impedance\s*([\d,]+)\s*-\s*([\d,]+)\s*(/cmm|/cumm)"),
        ("CBC", "Platelet Count", "Platelet Count", r"([\d,]+)\s*Platelet\s+Count\s+Elect\.\s*Impedance\s*([\d,]+)\s*-\s*([\d,]+)\s*(/cmm|/cumm)"),

        ("Glucose", "GLUCOSE (SUGAR) FASTING", "Fasting Blood Sugar", r"([\d.]+)\s*GLUCOSE\s*\(SUGAR\)\s*FASTING.*?Non-Diabetic:\s*<\s*([\d.]+)\s*(mg/dl|mg/dL)"),
        ("Glucose", "Glycosylated Hemoglobin (HbA1c)", "HbA1c", r"([\d.]+)\s*Glycosylated\s+Hemoglobin\s*\(HbA1c\)\s*,?\s*EDTA\s+WB\s*HPLCNon-Diabetic\s+Level:\s*<\s*([\d.]+)\s*(%)"),

        ("Kidney", "BUN, Serum", "BUN", r"([\d.]+)\s*BUN,\s*Serum\s+Calculated\s*([\d.]+)\s*-\s*([\d.]+)\s*(mg/dL|mg/dl)"),
        ("Kidney", "CREATININE, Serum", "Creatinine", r"([\d.]+)\s*CREATININE,\s*Serum.*?([\d.]+)\s*-\s*([\d.]+)\s*(mg/dL|mg/dl)"),
        ("Kidney", "URIC ACID, Serum", "Uric Acid", r"([\d.]+)\s*URIC\s+ACID,\s*Serum\s+Uricase\s*([\d.]+)\s*-\s*([\d.]+)\s*(mg/dL|mg/dl)"),

        ("Vitamins", "VITAMIN B12, Serum", "Vitamin B12", r"([\d.]+)\s*VITAMIN\s+B12,\s*Serum\s+ECLIA\s*([\d.]+)\s*-\s*([\d.]+)\s*(pg/mL|pg/ml)"),
        ("Vitamins", "25-hydroxy Vitamin D Serum", "Vitamin D", r"([\d.]+)\s*25\s*-?\s*hydroxy\s+Vitamin\s+D\s+Serum\s+ECLIA.*?Sufficiency:\s*([\d.]+)\s*-\s*([\d.]+)\s*(ng/ml|ng/mL)"),

        ("Lipids", "CHOLESTEROL, Serum", "Total Cholesterol", r"([\d.]+)\s*CHOLESTEROL,\s*Serum.*?Borderline\s+High:\s*([\d.]+)\s*-\s*([\d.]+)\s*(mg/dl|mg/dL)"),
        ("Lipids", "TRIGLYCERIDES, Serum", "Triglycerides", r"([\d.]+)\s*TRIGLYCERIDES,\s*Serum\s+GPO-PODNormal:\s*<\s*([\d.]+)\s*(mg/dl|mg/dL)"),
        ("Lipids", "HDL CHOLESTEROL", "HDL", r"([\d.]+)\s*HDL\s+CHOLESTEROL.*?Desirable:\s*>\s*([\d.]+)\s*(mg/dl|mg/dL)"),
        ("Lipids", "LDL CHOLESTEROL", "LDL", r"([\d.]+)\s*LDL\s+CHOLESTEROL.*?Near\s+optimal:\s*([\d.]+)\s*-\s*([\d.]+)\s*(mg/dl|mg/dL)"),
        ("Lipids", "VLDL CHOLESTEROL", "VLDL", r"([\d.]+)\s*VLDL\s+CHOLESTEROL.*?<\s*/?=?\s*([\d.]+)\s*(mg/dl|mg/dL)"),

        ("Thyroid", "Free T4", "Free T4", r"([\d.]+)\s*Free\s+T4\s+Serum\s+ECLIA\s*([\d.]+)\s*-\s*([\d.]+)\s*(pmol/L)"),
        ("Thyroid", "sensitiveTSH", "TSH", r"([\d.]+)\s*sensitiveTSH\s+Serum\s+ECLIA\s*([\d.]+)\s*-\s*([\d.]+)\s*(microIU/ml)"),
    ]

    value_before_rows = []

    for panel, raw_marker, canonical_hint, pattern_text in value_before_patterns:
        pattern = re.compile(pattern_text, flags=re.IGNORECASE)

        for match in pattern.finditer(compact_text):
            value = parse_float(match.group(1))

            if canonical_hint in {"Fasting Blood Sugar", "HbA1c", "HDL", "VLDL", "Triglycerides"}:
                reference_low = None
                reference_high = parse_float(match.group(2))
                unit = clean_text(match.group(3))
            else:
                reference_low = parse_float(match.group(2))
                reference_high = parse_float(match.group(3))
                unit = clean_text(match.group(4))

            if canonical_hint == "HDL":
                reference_low = parse_float(match.group(2))
                reference_high = None

            flag = calculate_flag(value, reference_low, reference_high)
            canonical_marker, category = canonicalize_marker(canonical_hint, panel)

            value_before_rows.append(
                {
                    "test_date": test_date,
                    "panel": panel,
                    "marker": canonical_hint,
                    "raw_marker": raw_marker,
                    "canonical_marker": canonical_marker,
                    "category": category,
                    "value": value,
                    "result_text": None,
                    "unit": unit,
                    "reference_low": reference_low,
                    "reference_high": reference_high,
                    "flag": flag,
                    "source_file": source_file,
                    "notes": "parsed_from_pdf_text_value_before_marker",
                }
            )

    if value_before_rows:
        value_before_markers = {row["canonical_marker"] for row in value_before_rows}

        results = [
            row
            for row in results
            if not (
                row["source_file"] == source_file
                and row["test_date"] == test_date
                and row["canonical_marker"] in value_before_markers
            )
        ]

        results.extend(value_before_rows)


    return results

def save_results(results):
    imported_at = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(DATABASE_PATH) as connection:
        create_table(connection)

        for row in results:
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
                    result_text,
                    unit,
                    reference_low,
                    reference_high,
                    flag,
                    source_file,
                    notes,
                    imported_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(test_date, marker, source_file)
                do update set
                    panel = excluded.panel,
                    raw_marker = excluded.raw_marker,
                    canonical_marker = excluded.canonical_marker,
                    category = excluded.category,
                    value = excluded.value,
                    result_text = excluded.result_text,
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
                    row["result_text"],
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


def parse_all_reports():
    if not PROCESSED_REPORTS_DIR.exists():
        raise FileNotFoundError(f"Processed reports folder not found: {PROCESSED_REPORTS_DIR}")

    all_results = []

    for path in sorted(PROCESSED_REPORTS_DIR.glob("*.txt")):
        all_results.extend(parse_report_file(path))

    save_results(all_results)

    print("Medical report parsing complete.")
    print(f"Imported/updated lab rows: {len(all_results)}")


if __name__ == "__main__":
    parse_all_reports()
