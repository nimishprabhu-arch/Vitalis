import json
import os
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "database" / "vitalis.db"
ENV_PATH = PROJECT_ROOT / ".env"
TABLE_NAME = "health_snapshots"


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


def load_env_file():
    if not ENV_PATH.exists():
        return

    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"'))


def clean_number(value, integer=False):
    if value is None:
        return None

    if integer:
        return int(round(float(value)))

    return float(value)


def read_latest_snapshot():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    row = cursor.execute(
        """
        select
            snapshot_date,
            saved_at,
            steps,
            distance_meters,
            active_calories,
            floors,
            average_heart_rate,
            minimum_heart_rate,
            maximum_heart_rate,
            resting_heart_rate,
            sleep_total_minutes,
            deep_sleep_minutes,
            rem_sleep_minutes,
            light_sleep_minutes,
            awake_minutes,
            sleep_session_count,
            workout_session_count,
            workout_total_duration_minutes,
            sleep_score,
            sleep_efficiency,
            physical_recovery,
            mental_recovery,
            energy_score,
            energy_sleep_score,
            energy_activity_score,
            heart_health_score,
            source
        from daily_health_snapshots
        order by snapshot_date desc
        limit 1
        """
    ).fetchone()

    connection.close()

    if row is None:
        raise RuntimeError("No health snapshots found in database.")

    snapshot = dict(row)

    for key in list(snapshot.keys()):
        if key in {"snapshot_date", "saved_at", "source"}:
            continue

        snapshot[key] = clean_number(
            snapshot[key],
            integer=key in INTEGER_FIELDS,
        )

    if not snapshot.get("source"):
        snapshot["source"] = "vitalis_laptop"

    return snapshot


def upload_to_supabase(snapshot, supabase_url, supabase_key):
    endpoint = (
        f"{supabase_url.rstrip('/')}/rest/v1/{TABLE_NAME}"
        "?on_conflict=snapshot_date"
    )

    data = json.dumps(snapshot).encode("utf-8")

    request = urllib.request.Request(
        endpoint,
        data=data,
        method="POST",
        headers={
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
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
    load_env_file()

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url:
        raise RuntimeError("SUPABASE_URL is missing from .env")

    if not supabase_key:
        raise RuntimeError("SUPABASE_KEY is missing from .env")

    snapshot = read_latest_snapshot()
    status, _ = upload_to_supabase(snapshot, supabase_url, supabase_key)

    print(f"Supabase upload status: {status}")
    print("Latest Vitalis snapshot uploaded to Supabase.")


if __name__ == "__main__":
    main()