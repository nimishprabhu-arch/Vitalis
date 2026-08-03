import sqlite3
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path("C:/Projects/Vitalis")
DATABASE_PATH = PROJECT_DIR / "database" / "vitalis.db"
SNAPSHOT_FOLDER = Path("G:/My Drive/Vitalis/snapshots")


def read_snapshot_file(path):
    data = {}

    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()

    return data


def to_int(value):
    if value == "" or value is None:
        return None
    return int(float(value))


def to_float(value):
    if value == "" or value is None:
        return None
    return float(value)


def import_snapshot(path):
    data = read_snapshot_file(path)
    imported_at = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO daily_health_snapshots (
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

                source_file,
                imported_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("date"),
                data.get("savedAt"),

                to_int(data.get("steps")),
                to_float(data.get("distanceMeters")),
                to_float(data.get("activeCalories")),
                to_float(data.get("floors")),

                to_float(data.get("averageHeartRate")),
                to_int(data.get("minimumHeartRate")),
                to_int(data.get("maximumHeartRate")),
                to_int(data.get("restingHeartRate")),

                to_int(data.get("sleepTotalMinutes")),
                to_int(data.get("deepSleepMinutes")),
                to_int(data.get("remSleepMinutes")),
                to_int(data.get("lightSleepMinutes")),
                to_int(data.get("awakeMinutes")),
                to_int(data.get("sleepSessionCount")),

                to_int(data.get("workoutSessionCount")),
                to_int(data.get("workoutTotalDurationMinutes")),

                str(path),
                imported_at,
            ),
        )


def main():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    if not SNAPSHOT_FOLDER.exists():
        raise FileNotFoundError(f"Snapshot folder not found: {SNAPSHOT_FOLDER}")

    files = sorted(SNAPSHOT_FOLDER.glob("*.txt"))

    if not files:
        print("No snapshot files found.")
        return

    for file in files:
        import_snapshot(file)
        print(f"Imported: {file.name}")

    print("Snapshot import complete.")


if __name__ == "__main__":
    main()