import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIR = Path("C:/Projects/Vitalis")
EXPORT_DIR = PROJECT_DIR / "data" / "samsung_export"
DATABASE_PATH = PROJECT_DIR / "database" / "vitalis.db"
EXERCISE_FILE_NAME = "com.samsung.shealth.exercise.20260803172487.csv"


EXERCISE_TYPE_LABELS = {
    "0": "Unknown",
    "1001": "Walking",
    "1002": "Running",
    "11007": "Other workout",
    "15002": "Weight training",
    "15003": "Circuit training",
    "15005": "Exercise machine",
    "15006": "Indoor bike",
}


def find_csv(prefix):
    matches = sorted(EXPORT_DIR.glob(f"{prefix}*.csv"))
    return matches[-1] if matches else None


def read_samsung_csv(path):
    if path is None:
        return []

    rows = []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)

        try:
            next(reader)
            headers = next(reader)
        except StopIteration:
            return []

        header_count = len(headers)

        for row in reader:
            if not row:
                continue

            if len(row) > header_count:
                row = row[:header_count]

            if len(row) < header_count:
                row = row + [""] * (header_count - len(row))

            rows.append(dict(zip(headers, row)))

    return rows


def parse_datetime(value):
    if not value:
        return None

    value = str(value).strip()[:19]

    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def to_float(value):
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    try:
        return float(value)
    except ValueError:
        return None


def to_int(value):
    number = to_float(value)

    if number is None:
        return None

    return int(number)


def ensure_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS workouts (
            workout_id TEXT PRIMARY KEY,
            workout_date TEXT,
            start_time TEXT,
            end_time TEXT,

            exercise_type_code TEXT,
            exercise_type_label TEXT,

            duration_minutes REAL,
            calories REAL,
            distance_meters REAL,

            average_heart_rate REAL,
            minimum_heart_rate REAL,
            maximum_heart_rate REAL,

            source TEXT,
            raw_json TEXT,
            imported_at TEXT
        )
        """
    )

    connection.commit()
    connection.close()


def import_workouts():
    path = EXPORT_DIR / EXERCISE_FILE_NAME
    rows = read_samsung_csv(path)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    imported_count = 0
    imported_at = datetime.now(timezone.utc).isoformat()

    for row in rows:
        workout_id = row.get("com.samsung.health.exercise.datauuid")

        if not workout_id:
            continue

        start_time = parse_datetime(row.get("com.samsung.health.exercise.start_time"))
        end_time = parse_datetime(row.get("com.samsung.health.exercise.end_time"))

        if start_time is None:
            continue

        workout_date = start_time.date().isoformat()

        duration_ms = to_float(row.get("com.samsung.health.exercise.duration"))
        duration_minutes = duration_ms / 60000 if duration_ms is not None else None

        exercise_type_code = str(row.get("com.samsung.health.exercise.exercise_type") or "").strip()
        exercise_type_label = EXERCISE_TYPE_LABELS.get(exercise_type_code, f"Samsung type {exercise_type_code}")

        cursor.execute(
            """
            INSERT INTO workouts (
                workout_id,
                workout_date,
                start_time,
                end_time,

                exercise_type_code,
                exercise_type_label,

                duration_minutes,
                calories,
                distance_meters,

                average_heart_rate,
                minimum_heart_rate,
                maximum_heart_rate,

                source,
                raw_json,
                imported_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(workout_id) DO UPDATE SET
                workout_date = excluded.workout_date,
                start_time = excluded.start_time,
                end_time = excluded.end_time,

                exercise_type_code = excluded.exercise_type_code,
                exercise_type_label = excluded.exercise_type_label,

                duration_minutes = excluded.duration_minutes,
                calories = excluded.calories,
                distance_meters = excluded.distance_meters,

                average_heart_rate = excluded.average_heart_rate,
                minimum_heart_rate = excluded.minimum_heart_rate,
                maximum_heart_rate = excluded.maximum_heart_rate,

                source = excluded.source,
                raw_json = excluded.raw_json,
                imported_at = excluded.imported_at
            """,
            (
                workout_id,
                workout_date,
                start_time.isoformat(),
                end_time.isoformat() if end_time else None,

                exercise_type_code,
                exercise_type_label,

                duration_minutes,
                to_float(row.get("com.samsung.health.exercise.calorie")),
                to_float(row.get("com.samsung.health.exercise.distance")),

                to_float(row.get("com.samsung.health.exercise.mean_heart_rate")),
                to_float(row.get("com.samsung.health.exercise.min_heart_rate")),
                to_float(row.get("com.samsung.health.exercise.max_heart_rate")),

                "samsung_historical_export",
                json.dumps(row, ensure_ascii=False),
                imported_at,
            ),
        )

        imported_count += 1

    connection.commit()
    connection.close()

    print(f"Imported/updated workouts: {imported_count}")


def update_daily_workout_summaries():
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE daily_health_snapshots
        SET
            workout_session_count = (
                SELECT COUNT(*)
                FROM workouts
                WHERE workouts.workout_date = daily_health_snapshots.snapshot_date
            ),
            workout_total_duration_minutes = (
                SELECT COALESCE(SUM(duration_minutes), 0)
                FROM workouts
                WHERE workouts.workout_date = daily_health_snapshots.snapshot_date
            )
        WHERE snapshot_date IN (
            SELECT DISTINCT workout_date
            FROM workouts
        )
        """
    )

    connection.commit()
    connection.close()

    print("Updated daily workout summaries.")


def main():
    if not EXPORT_DIR.exists():
        raise FileNotFoundError(f"Samsung export folder not found: {EXPORT_DIR}")

    ensure_database()
    import_workouts()
    update_daily_workout_summaries()

    print("--------------------------------")
    print("Samsung workout import complete.")


if __name__ == "__main__":
    main()