import csv
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIR = Path("C:/Projects/Vitalis")
EXPORT_DIR = PROJECT_DIR / "data" / "samsung_export"
DATABASE_PATH = PROJECT_DIR / "database" / "vitalis.db"

STEP_FILE_PREFIX = "com.samsung.shealth.step_daily_trend"
HEART_RATE_FILE_PREFIX = "com.samsung.shealth.tracker.heart_rate"
SLEEP_COMBINED_FILE_PREFIX = "com.samsung.shealth.sleep_combined"
SLEEP_STAGE_FILE_PREFIX = "com.samsung.health.sleep_stage"
VITALITY_SCORE_FILE_PREFIX = "com.samsung.shealth.vitality_score"
HEART_HEALTH_SCORE_FILE_PREFIX = "com.samsung.shealth.heart_health_score"

SLEEP_STAGE_MAP = {
    40001: "awake_minutes",
    40002: "light_sleep_minutes",
    40003: "deep_sleep_minutes",
    40004: "rem_sleep_minutes",
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

            row = row[:header_count] if len(row) > header_count else row
            row = row + [""] * (header_count - len(row)) if len(row) < header_count else row

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


def to_int(value):
    number = to_float(value)

    if number is None:
        return None

    return int(number)


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


def date_from_datetime_text(value):
    parsed = parse_datetime(value)
    return parsed.date().isoformat() if parsed else None


def load_steps():
    rows = read_samsung_csv(find_csv(STEP_FILE_PREFIX))
    daily = {}

    for row in rows:
        snapshot_date = date_from_datetime_text(row.get("day_time"))

        if snapshot_date is None:
            continue

        daily[snapshot_date] = {
            "steps": to_int(row.get("count")),
            "distance_meters": to_float(row.get("distance")),
            "active_calories": to_float(row.get("calorie")),
            "floors": None,
        }

    print(f"Loaded step rows: {len(daily)}")
    return daily


def load_heart_rate():
    rows = read_samsung_csv(find_csv(HEART_RATE_FILE_PREFIX))
    grouped = defaultdict(list)

    for row in rows:
        snapshot_date = date_from_datetime_text(row.get("com.samsung.health.heart_rate.start_time"))
        heart_rate = to_float(row.get("com.samsung.health.heart_rate.heart_rate"))

        if snapshot_date and heart_rate and heart_rate > 0:
            grouped[snapshot_date].append(heart_rate)

    daily = {}

    for snapshot_date, values in grouped.items():
        daily[snapshot_date] = {
            "average_heart_rate": sum(values) / len(values),
            "minimum_heart_rate": int(min(values)),
            "maximum_heart_rate": int(max(values)),
            "resting_heart_rate": None,
        }

    print(f"Loaded heart rate days: {len(daily)}")
    return daily


def load_sleep_combined():
    rows = read_samsung_csv(find_csv(SLEEP_COMBINED_FILE_PREFIX))

    grouped = defaultdict(
        lambda: {
            "sleep_total_minutes": 0,
            "rem_sleep_minutes": 0,
            "light_sleep_minutes": 0,
            "deep_sleep_minutes": None,
            "awake_minutes": None,
            "sleep_session_count": 0,
            "sleep_score": None,
            "sleep_efficiency": None,
            "physical_recovery": None,
            "mental_recovery": None,
        }
    )

    for row in rows:
        start_time = parse_datetime(row.get("start_time"))
        end_time = parse_datetime(row.get("end_time"))

        if start_time is None:
            continue

        snapshot_date = start_time.date().isoformat()

        sleep_duration = to_int(row.get("sleep_duration"))

        if sleep_duration is None and end_time is not None:
            sleep_duration = int((end_time - start_time).total_seconds() // 60)

        if sleep_duration and sleep_duration > 0:
            grouped[snapshot_date]["sleep_total_minutes"] += sleep_duration

        light_duration = to_int(row.get("total_light_duration"))
        rem_duration = to_int(row.get("total_rem_duration"))

        if light_duration and light_duration > 0:
            grouped[snapshot_date]["light_sleep_minutes"] += light_duration

        if rem_duration and rem_duration > 0:
            grouped[snapshot_date]["rem_sleep_minutes"] += rem_duration

        grouped[snapshot_date]["sleep_session_count"] += 1

        for column, source in [
            ("sleep_score", "sleep_score"),
            ("sleep_efficiency", "efficiency"),
            ("physical_recovery", "physical_recovery"),
            ("mental_recovery", "mental_recovery"),
        ]:
            value = to_float(row.get(source))
            if value is not None:
                grouped[snapshot_date][column] = value

    print(f"Loaded sleep days: {len(grouped)}")
    return dict(grouped)


def load_sleep_stages():
    rows = read_samsung_csv(find_csv(SLEEP_STAGE_FILE_PREFIX))

    grouped = defaultdict(
        lambda: {
            "deep_sleep_minutes": 0,
            "rem_sleep_minutes": 0,
            "light_sleep_minutes": 0,
            "awake_minutes": 0,
        }
    )

    for row in rows:
        start_time = parse_datetime(row.get("start_time"))
        end_time = parse_datetime(row.get("end_time"))
        stage = to_int(row.get("stage"))

        if start_time is None or end_time is None or stage not in SLEEP_STAGE_MAP:
            continue

        duration_minutes = int((end_time - start_time).total_seconds() // 60)

        if duration_minutes <= 0:
            continue

        snapshot_date = start_time.date().isoformat()
        grouped[snapshot_date][SLEEP_STAGE_MAP[stage]] += duration_minutes

    daily = {}

    for snapshot_date, values in grouped.items():
        daily[snapshot_date] = {
            key: value if value > 0 else None
            for key, value in values.items()
        }

    print(f"Loaded sleep stage days: {len(daily)}")
    return daily


def load_vitality_scores():
    rows = read_samsung_csv(find_csv(VITALITY_SCORE_FILE_PREFIX))
    daily = {}

    for row in rows:
        snapshot_date = date_from_datetime_text(row.get("day_time"))

        if snapshot_date is None:
            continue

        daily[snapshot_date] = {
            "energy_score": to_float(row.get("total_score")),
            "energy_sleep_score": to_float(row.get("sleep_score")),
            "energy_activity_score": to_float(row.get("activity_score")),
        }

    print(f"Loaded vitality score days: {len(daily)}")
    return daily


def load_heart_health_scores():
    rows = read_samsung_csv(find_csv(HEART_HEALTH_SCORE_FILE_PREFIX))
    daily = {}

    for row in rows:
        snapshot_date = date_from_datetime_text(row.get("day_time"))

        if snapshot_date is None:
            continue

        daily[snapshot_date] = {
            "heart_health_score": to_float(row.get("total_score")),
        }

    print(f"Loaded heart health score days: {len(daily)}")
    return daily


def merge_daily_data(*sources):
    merged = defaultdict(dict)

    for source in sources:
        for snapshot_date, values in source.items():
            merged[snapshot_date].update(values)

    return dict(merged)


def ensure_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_health_snapshots (
            snapshot_date TEXT PRIMARY KEY,
            saved_at TEXT,
            source TEXT,

            steps INTEGER,
            distance_meters REAL,
            active_calories REAL,
            floors INTEGER,

            average_heart_rate REAL,
            minimum_heart_rate INTEGER,
            maximum_heart_rate INTEGER,
            resting_heart_rate INTEGER,

            sleep_total_minutes INTEGER,
            deep_sleep_minutes INTEGER,
            rem_sleep_minutes INTEGER,
            light_sleep_minutes INTEGER,
            awake_minutes INTEGER,
            sleep_session_count INTEGER,

            sleep_score REAL,
            sleep_efficiency REAL,
            physical_recovery REAL,
            mental_recovery REAL,

            energy_score REAL,
            energy_sleep_score REAL,
            energy_activity_score REAL,
            heart_health_score REAL,

            workout_session_count INTEGER,
            workout_total_duration_minutes INTEGER,

            raw_json TEXT,
            imported_at TEXT
        )
        """
    )

    existing_columns = [row[1] for row in cursor.execute("PRAGMA table_info(daily_health_snapshots)")]

    columns_to_add = [
        ("source", "TEXT"),
        ("raw_json", "TEXT"),
        ("imported_at", "TEXT"),
        ("sleep_score", "REAL"),
        ("sleep_efficiency", "REAL"),
        ("physical_recovery", "REAL"),
        ("mental_recovery", "REAL"),
        ("energy_score", "REAL"),
        ("energy_sleep_score", "REAL"),
        ("energy_activity_score", "REAL"),
        ("heart_health_score", "REAL"),
    ]

    for column_name, column_type in columns_to_add:
        if column_name not in existing_columns:
            cursor.execute(f"ALTER TABLE daily_health_snapshots ADD COLUMN {column_name} {column_type}")

    connection.commit()
    connection.close()


def upsert_snapshot(snapshot_date, values):
    saved_at = f"{snapshot_date}T00:00:00"
    imported_at = datetime.now(timezone.utc).isoformat()

    raw_json = json.dumps(
        {
            "snapshot_date": snapshot_date,
            "source": "samsung_historical_export",
            "values": values,
        },
        ensure_ascii=False,
    )

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO daily_health_snapshots (
            snapshot_date,
            saved_at,
            source,

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

            sleep_score,
            sleep_efficiency,
            physical_recovery,
            mental_recovery,

            energy_score,
            energy_sleep_score,
            energy_activity_score,
            heart_health_score,

            workout_session_count,
            workout_total_duration_minutes,

            raw_json,
            imported_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(snapshot_date) DO UPDATE SET
            saved_at = excluded.saved_at,
            source = excluded.source,

            steps = COALESCE(excluded.steps, daily_health_snapshots.steps),
            distance_meters = COALESCE(excluded.distance_meters, daily_health_snapshots.distance_meters),
            active_calories = COALESCE(excluded.active_calories, daily_health_snapshots.active_calories),
            floors = COALESCE(excluded.floors, daily_health_snapshots.floors),

            average_heart_rate = COALESCE(excluded.average_heart_rate, daily_health_snapshots.average_heart_rate),
            minimum_heart_rate = COALESCE(excluded.minimum_heart_rate, daily_health_snapshots.minimum_heart_rate),
            maximum_heart_rate = COALESCE(excluded.maximum_heart_rate, daily_health_snapshots.maximum_heart_rate),
            resting_heart_rate = COALESCE(excluded.resting_heart_rate, daily_health_snapshots.resting_heart_rate),

            sleep_total_minutes = COALESCE(excluded.sleep_total_minutes, daily_health_snapshots.sleep_total_minutes),
            deep_sleep_minutes = COALESCE(excluded.deep_sleep_minutes, daily_health_snapshots.deep_sleep_minutes),
            rem_sleep_minutes = COALESCE(excluded.rem_sleep_minutes, daily_health_snapshots.rem_sleep_minutes),
            light_sleep_minutes = COALESCE(excluded.light_sleep_minutes, daily_health_snapshots.light_sleep_minutes),
            awake_minutes = COALESCE(excluded.awake_minutes, daily_health_snapshots.awake_minutes),
            sleep_session_count = COALESCE(excluded.sleep_session_count, daily_health_snapshots.sleep_session_count),

            sleep_score = COALESCE(excluded.sleep_score, daily_health_snapshots.sleep_score),
            sleep_efficiency = COALESCE(excluded.sleep_efficiency, daily_health_snapshots.sleep_efficiency),
            physical_recovery = COALESCE(excluded.physical_recovery, daily_health_snapshots.physical_recovery),
            mental_recovery = COALESCE(excluded.mental_recovery, daily_health_snapshots.mental_recovery),

            energy_score = COALESCE(excluded.energy_score, daily_health_snapshots.energy_score),
            energy_sleep_score = COALESCE(excluded.energy_sleep_score, daily_health_snapshots.energy_sleep_score),
            energy_activity_score = COALESCE(excluded.energy_activity_score, daily_health_snapshots.energy_activity_score),
            heart_health_score = COALESCE(excluded.heart_health_score, daily_health_snapshots.heart_health_score),

            workout_session_count = COALESCE(excluded.workout_session_count, daily_health_snapshots.workout_session_count),
            workout_total_duration_minutes = COALESCE(excluded.workout_total_duration_minutes, daily_health_snapshots.workout_total_duration_minutes),

            raw_json = excluded.raw_json,
            imported_at = excluded.imported_at
        """,
        (
            snapshot_date,
            saved_at,
            "samsung_historical_export",

            values.get("steps"),
            values.get("distance_meters"),
            values.get("active_calories"),
            values.get("floors"),

            values.get("average_heart_rate"),
            values.get("minimum_heart_rate"),
            values.get("maximum_heart_rate"),
            values.get("resting_heart_rate"),

            values.get("sleep_total_minutes"),
            values.get("deep_sleep_minutes"),
            values.get("rem_sleep_minutes"),
            values.get("light_sleep_minutes"),
            values.get("awake_minutes"),
            values.get("sleep_session_count"),

            values.get("sleep_score"),
            values.get("sleep_efficiency"),
            values.get("physical_recovery"),
            values.get("mental_recovery"),

            values.get("energy_score"),
            values.get("energy_sleep_score"),
            values.get("energy_activity_score"),
            values.get("heart_health_score"),

            values.get("workout_session_count"),
            values.get("workout_total_duration_minutes"),

            raw_json,
            imported_at,
        ),
    )

    connection.commit()
    connection.close()


def main():
    if not EXPORT_DIR.exists():
        raise FileNotFoundError(f"Samsung export folder not found: {EXPORT_DIR}")

    ensure_database()

    merged = merge_daily_data(
        load_steps(),
        load_heart_rate(),
        load_sleep_combined(),
        load_sleep_stages(),
        load_vitality_scores(),
        load_heart_health_scores(),
    )

    for snapshot_date, values in sorted(merged.items()):
        upsert_snapshot(snapshot_date, values)

    print("--------------------------------")
    print("Samsung historical import complete.")
    print(f"Imported/updated daily snapshots: {len(merged)}")


if __name__ == "__main__":
    main()