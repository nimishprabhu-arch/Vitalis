import json
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "database" / "vitalis.db"

SUPABASE_URL = "https://ltnlhxsdmcsjpcpxvvxl.supabase.co"
SUPABASE_KEY = "sb_publishable_U55ZW10vDw7fX-kVmWVl0w_8nXnsrOW"

TABLE_NAME = "workouts"

COLUMNS = [
    "workout_id",
    "workout_date",
    "start_time",
    "end_time",
    "exercise_type_code",
    "exercise_type_label",
    "duration_minutes",
    "calories",
    "distance_meters",
    "average_heart_rate",
    "minimum_heart_rate",
    "maximum_heart_rate",
    "source",
    "raw_json",
    "imported_at",
]


def fetch_rows():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            f"""
            select {", ".join(COLUMNS)}
            from workouts
            order by workout_date asc, start_time asc
            """
        ).fetchall()

    return [dict(row) for row in rows]


def upload_rows(rows):
    if not rows:
        return 0

    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?on_conflict=workout_id"

    request = urllib.request.Request(
        url,
        data=json.dumps(rows).encode("utf-8"),
        method="POST",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            response.read()
            return response.status
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase error {error.code}: {body}") from error


def main():
    if "PASTE_YOUR" in SUPABASE_KEY:
        raise RuntimeError("Error SUpabase key")

    rows = fetch_rows()
    status = upload_rows(rows)

    print(f"Supabase upload status: {status}")
    print(f"Uploaded/updated workout rows: {len(rows)}")


if __name__ == "__main__":
    main()