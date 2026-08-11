import json
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "database" / "vitalis.db"

SUPABASE_URL = "https://ltnlhxsdmcsjpcpxvvxl.supabase.co"
SUPABASE_KEY = "sb_publishable_U55ZW10vDw7fX-kVmWVl0w_8nXnsrOW"
TABLE_NAME = "health_snapshots"

BATCH_SIZE = 250

COLUMNS = [
    "snapshot_date",
    "saved_at",
    "steps",
    "distance_meters",
    "active_calories",
    "active_time_minutes",
    "rest_calories",
    "exercise_calories",
    "total_burned_calories",
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
    "workout_total_calories",
    "workout_distance_meters",
    "workout_average_heart_rate",
    "workout_minimum_heart_rate",
    "workout_maximum_heart_rate",
    "workout_low_intensity_minutes",
    "workout_weight_control_minutes",
    "workout_aerobic_minutes",
    "workout_anaerobic_minutes",
    "workout_max_intensity_minutes",
    "sleep_score",
    "sleep_efficiency",
    "physical_recovery",
    "mental_recovery",
    "energy_score",
    "energy_sleep_score",
    "energy_activity_score",
    "heart_health_score",
    "vitalis_readiness_score",
    "vitalis_sleep_quality_score",
    "vitalis_recovery_score",
    "vitalis_training_load_score",
    "vitalis_coach_note",
    "source",
]


INTEGER_COLUMNS = {
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
    "workout_low_intensity_minutes",
    "workout_weight_control_minutes",
    "workout_aerobic_minutes",
    "workout_anaerobic_minutes",
    "workout_max_intensity_minutes",
}


def clean_row(row):
    cleaned = {}

    for key, value in dict(row).items():
        if key not in COLUMNS:
            continue

        if key in INTEGER_COLUMNS and value is not None:
            cleaned[key] = int(round(float(value)))
        else:
            cleaned[key] = value

    return cleaned


def load_rows():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row

        available_columns = {
            row["name"]
            for row in connection.execute("pragma table_info(daily_health_snapshots)")
        }

        selected_columns = [column for column in COLUMNS if column in available_columns]

        query = f"""
            SELECT {", ".join(selected_columns)}
            FROM daily_health_snapshots
            ORDER BY snapshot_date ASC
        """

        return [clean_row(row) for row in connection.execute(query).fetchall()]


def upload_batch(rows):
    if not rows:
        return

    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?on_conflict=snapshot_date"

    request = urllib.request.Request(
        url,
        data=json.dumps(rows).encode("utf-8"),
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            response.read()
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase error {error.code}: {body}") from error


def main():
    if SUPABASE_KEY == "PASTE_YOUR_SUPABASE_KEY_HERE":
        raise RuntimeError("Paste your Supabase key before running this script.")

    rows = load_rows()
    total = len(rows)

    print(f"Snapshots to upload: {total}")

    for index in range(0, total, BATCH_SIZE):
        batch = rows[index:index + BATCH_SIZE]
        upload_batch(batch)
        print(f"Uploaded: {min(index + BATCH_SIZE, total)}/{total}")

    print("Historical Supabase upload complete.")


if __name__ == "__main__":
    main()