import datetime
import sqlite3

DB = "database/vitalis.db"
SOURCE_2067 = "20674480_DvMMxFEDrtvxbhpWG9T3Ew.pdf"
SOURCE_2026 = "nimish prabhu-1.pdf"

now = datetime.datetime.now(datetime.UTC).isoformat()

rows = [
    ("2026-03-06", "Glucose", "HbA1c", "HbA1c", "HbA1c", 4.8, "%", None, 5.7, "normal", SOURCE_2067, "manual_date_corrected_from_pdf_text", None),
    ("2026-03-06", "Vitamins", "Vitamin D", "Vitamin D", "Vitamin D", 16.2, "ng/ml", 30, 100, "low", SOURCE_2067, "manual_date_corrected_from_pdf_text", None),
    ("2026-03-06", "Vitamins", "Vitamin B12", "Vitamin B12", "Vitamin B12", 169, "pg/ml", 222, 1439, "low", SOURCE_2067, "manual_date_corrected_from_pdf_text", None),
    ("2026-06-19", "Infectious Disease", "HBsAg", "HBsAg", "HBsAg", None, None, None, None, "Non Reactive", SOURCE_2026, "manual_verified_from_pdf_text", "Non Reactive"),
    ("2026-06-19", "Infectious Disease", "HCV", "HCV Antibodies", "HCV", None, None, None, None, "Non Reactive", SOURCE_2026, "manual_verified_from_pdf_text", "Non Reactive"),
    ("2026-06-19", "Infectious Disease", "HIV", "HIV 1+O/2 Antibodies & p24 Antigen", "HIV", None, None, None, None, "Non Reactive", SOURCE_2026, "manual_verified_from_pdf_text", "Non Reactive"),
]

with sqlite3.connect(DB) as connection:
    connection.execute(
        """
        delete from medical_lab_results
        where source_file = ?
          and test_date = 'unknown'
          and canonical_marker in ('HbA1c', 'Vitamin D', 'Vitamin B12')
        """,
        (SOURCE_2067,),
    )

    connection.executemany(
        """
        insert into medical_lab_results (
            test_date, category, marker, raw_marker, canonical_marker,
            value, unit, reference_low, reference_high, flag,
            source_file, notes, imported_at, result_text
        )
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(test_date, marker, source_file) do update set
            category = excluded.category,
            raw_marker = excluded.raw_marker,
            canonical_marker = excluded.canonical_marker,
            value = excluded.value,
            unit = excluded.unit,
            reference_low = excluded.reference_low,
            reference_high = excluded.reference_high,
            flag = excluded.flag,
            notes = excluded.notes,
            imported_at = excluded.imported_at,
            result_text = excluded.result_text
        """,
        [row[:12] + (now, row[12]) for row in rows],
    )

print("Fixed unknown-date and empty-result lab rows.")