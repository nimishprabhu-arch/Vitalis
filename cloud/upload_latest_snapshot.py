import json
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_DIR = Path("C:/Projects/Vitalis")
DATABASE_PATH = PROJECT_DIR / "database" / "vitalis.db"
ENV_PATH = PROJECT_DIR / ".env"


def load_env():
    if not ENV_PATH.exists():
        raise RuntimeError(f"Missing .env file: {ENV_PATH}")

    values = {}

    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()

    return values


def latest_snapshot():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row

        row = connection.execute(
            """
            SELECT *
            FROM daily_health_snapshots
            ORDER BY snapshot_date DESC
            LIMIT 1
            """
        ).fetchone()

    if row is None:
        raise RuntimeError("No health snapshots found in local database.")

    return {
        "snapshot_date": row["snapshot_date"],
        "saved_at": row["saved_at"],
        "steps": row["steps"],
        "distance_meters": row["distance_meters"],
        "active_calories": row["active_calories"],
        "floors": row["floors"],
        "average_heart_rate": row["average_heart_rate"],
        "minimum_heart_rate": row["minimum_heart_rate"],
        "maximum_heart_rate": row["maximum_heart_rate"],
        "resting_heart_rate": row["resting_heart_rate"],
        "sleep_total_minutes": row["sleep_total_minutes"],
        "deep_sleep_minutes": row["deep_sleep_minutes"],
        "rem_sleep_minutes": row["rem_sleep_minutes"],
        "light_sleep_minutes": row["light_sleep_minutes"],
        "awake_minutes": row["awake_minutes"],
        "sleep_session_count": row["sleep_session_count"],
        "workout_session_count": row["workout_session_count"],
        "workout_total_duration_minutes": row["workout_total_duration_minutes"],
        "source": "vitalis_laptop",
    }


def upload_to_supabase(snapshot, supabase_url, supabase_key):
    endpoint = f"{supabase_url}/rest/v1/health_snapshots?on_conflict=snapshot_date"

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
    env = load_env()

    supabase_url = env.get("SUPABASE_URL")
    supabase_key = env.get("SUPABASE_KEY")

    if not supabase_url:
        raise RuntimeError("SUPABASE_URL is missing in .env")

    if not supabase_key:
        raise RuntimeError("SUPABASE_KEY is missing in .env")

    snapshot = latest_snapshot()
    status, body = upload_to_supabase(snapshot, supabase_url, supabase_key)

    print(f"Supabase upload status: {status}")

    if body:
        print(body)

    print("Latest Vitalis snapshot uploaded to Supabase.")


if __name__ == "__main__":
    main()