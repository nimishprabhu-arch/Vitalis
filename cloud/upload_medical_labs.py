import json
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "database" / "vitalis.db"

SUPABASE_URL = "https://ltnlhxsdmcsjpcpxvvxl.supabase.co"
SUPABASE_KEY = "sb_publishable_U55ZW10vDw7fX-kVmWVl0w_8nXnsrOW"
TABLE_NAME = "medical_lab_results"


def load_rows():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            select
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
                notes
            from medical_lab_results
            order by test_date asc, canonical_marker asc
            """
        ).fetchall()

    output_rows = []

    for row in rows:
        if not row["test_date"] or row["test_date"] == "unknown":
            continue

        upload_row = dict(row)

        if (
            upload_row.get("source_file") == "227437_570793.pdf"
            and upload_row.get("test_date") == "2023-12-14"
            and upload_row.get("canonical_marker") == "LDL"
        ):
            upload_row["value"] = 160
            upload_row["unit"] = "mg/dL"
            upload_row["reference_low"] = 100
            upload_row["reference_high"] = 129
            upload_row["flag"] = "high"
            upload_row["raw_marker"] = "LDL"
            upload_row["marker"] = "LDL"
            upload_row["notes"] = "corrected_known_lipid_layout"

        output_rows.append(upload_row)

    return output_rows

def upload_rows(rows):
    if not rows:
        return 200, "No rows to upload."

    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?on_conflict=test_date,marker,source_file"

    data = json.dumps(rows).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8")
        raise RuntimeError(f"Supabase error {error.code}: {body}") from error


def main():
    if SUPABASE_KEY == "PASTE_YOUR_SUPABASE_PUBLISHABLE_KEY_HERE":
        raise RuntimeError("Paste your Supabase publishable key before running this script.")

    rows = load_rows()
    status, _ = upload_rows(rows)

    print(f"Supabase upload status: {status}")
    print(f"Uploaded/updated medical lab rows: {len(rows)}")


if __name__ == "__main__":
    main()
