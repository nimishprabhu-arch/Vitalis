import json
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "database" / "vitalis.db"

SUPABASE_URL = "https://ltnlhxsdmcsjpcpxvvxl.supabase.co"
SUPABASE_KEY = "sb_publishable_U55ZW10vDw7fX-kVmWVl0w_8nXnsrOW"

TABLE_NAME = "health_snapshots"
BATCH_SIZE = 250

INTEGER_FIELDS = {
    "steps",
    "minimum_heart_rate",
    "maximum_heart_rate",
    "resting_heart_rate",
    "sleep_total_minutes",
    "deep_sleep_minutes",
    "rem_sleep_minutes",
    "light_sleep_minutes",
    "awake_minutes",
    "sleep_session_count",
    "workout_session_count",
    "workout_total_duration_minutes",
}

REAL_FIELDS = {
    "distance_meters",
    "active_calories",
    "floors",
    "average_heart_rate",
    "sleep_score",
    "sleep_efficiency",
    "physical_recovery",
    "mental_recovery",
    "energy_score",
    "energy_sleep_score",
    "energy_activity_score",
    "heart_health_score",
}

FIELDS = [
    "snapshot_date",
    "saved_at",
    "steps",
    "distance_meters",
    "active_calories",
    "floors",
    "average_heart_rate",
    "minimum_heart_rate",
    "maximum_heart_rate",
    "resting_heart_rate",
    "sleep_total_minutes",
    "deep_sleep_minutes",
    "rem_sleep_minutes",
    "light_sleep_minutes",
    "awake_minutes",
    "sleep_session_count",
    "workout_session_count",
    "workout_total_duration_minutes",
    "source",
    "sleep_score",
    "sleep_efficiency",
    "physical_recovery",
    "mental_recovery",
    "energy_score",
    "energy_sleep_score",
    "energy_activity_score",
    "heart_health_score",
]

def normalize_value(field, value):
    if value is None:
        return None

    if field in INTEGER_FIELDS:
        try:
            return int(round(float(value)))
        except (TypeError, ValueError):
            return None

    if field in REAL_FIELDS:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    return value

def load_snapshots():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    rows = connection.execute(
        f"""
        SELECT {", ".join(FIELDS)}
        FROM daily_health_snapshots
        ORDER BY snapshot_date ASC
        """
    ).fetchall()

    connection.close()

    snapshots = []

    for row in rows:
        snapshot = {}
        for field in FIELDS:
            snapshot[field] = normalize_value(field, row[field])
        snapshots.append(snapshot)

    return snapshots

def upload_batch(batch, supabase_url, supabase_key):
    url = f"{supabase_url}/rest/v1/{TABLE_NAME}?on_conflict=snapshot_date"

    data = json.dumps(batch).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
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

    snapshots = load_snapshots()

    print(f"Snapshots to upload: {len(snapshots)}")

    uploaded = 0

    for index in range(0, len(snapshots), BATCH_SIZE):
        batch = snapshots[index:index + BATCH_SIZE]
        upload_batch(batch, SUPABASE_URL, SUPABASE_KEY)

        uploaded += len(batch)
        print(f"Uploaded: {uploaded}/{len(snapshots)}")

    print("Historical Supabase upload complete.")

if __name__ == "__main__":
    main()