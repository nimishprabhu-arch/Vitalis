import csv
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path("C:/Projects/Vitalis")
EXPORT_DIR = PROJECT_DIR / "data" / "samsung_export"
DATABASE_PATH = PROJECT_DIR / "database" / "vitalis.db"

STEP_FILE_PREFIX = "com.samsung.shealth.step_daily_trend"
HEART_FILE_PREFIX = "com.samsung.shealth.tracker.heart_rate"
SLEEP_FILE_PREFIX = "com.samsung.shealth.sleep_combined"


def find_csv(prefix):
    matches = list(EXPORT_DIR.glob(f"{prefix}*.csv"))

    if not matches:
        raise FileNotFoundError(f"No Samsung export file found for: {prefix}")

    return matches[0]


def parse_datetime(value):
    if not value:
        return None

    return datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S")


def date_from_datetime(value):
    parsed = parse_datetime(value)

    if parsed is None:
        return None

    return parsed.date().isoformat()


def to_int(value):
    if value in (None, ""):
        return None

    return int(float(value))


def to_float(value):
    if value in (None, ""):
        return None

    return float(value)


def read_samsung_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)

        metadata = next(reader, None)
        headers = next(reader, None)

        if headers is None:
            return []

        rows = []

        for raw_row in reader:
            if not raw_row:
                continue

            if len(raw_row) > len(headers):
                raw_row = raw_row[: len(headers)]

            row = dict(zip(headers, raw_row))
            rows.append(row)

        return rows


def load_steps():
    path = find_csv(STEP_FILE_PREFIX)
    rows = read_samsung_csv(path)

    daily = {}

    for row in rows:
        snapshot_date = date_from_datetime(row.get("day_time"))

        if not snapshot_date:
            continue

        daily[snapshot_date] = {
            "steps": to_int(row.get("count")),
            "distance_meters": to_float(row.get("distance")),
            "active_calories": to_float(row.get("calorie")),
        }

    print(f"Loaded step rows: {len(daily)}")
    return daily


def load_heart_rate():
    path = find_csv(HEART_FILE_PREFIX)
    rows = read_samsung_csv(path)

    grouped = defaultdict(list)

    for row in rows:
        snapshot_date = date_from_datetime(row.get("com.samsung.health.heart_rate.start_time"))
        heart_rate = to_float(row.get("com.samsung.health.heart_rate.heart_rate"))

        if not snapshot_date or heart_rate is None or heart_rate <= 0:
            continue

        grouped[snapshot_date].append(heart_rate)

    daily = {}

    for snapshot_date, values in grouped.items():
        daily[snapshot_date] = {
            "average_heart_rate": sum(values) / len(values),
            "minimum_heart_rate": int(min(values)),
            "maximum_heart_rate": int(max(values)),
        }

    print(f"Loaded heart rate days: {len(daily)}")
    return daily


def load_sleep():
    path = find_csv(SLEEP_FILE_PREFIX)
    rows = read_samsung_csv(path)

    daily = {}

    for row in rows:
        start_time = parse_datetime(row.get("start_time"))
        end_time = parse_datetime(row.get("end_time"))

        if start_time is None:
            continue

        snapshot_date = start_time.date().isoformat()

        sleep_duration = to_int(row.get("sleep_duration"))
        light_minutes = to_int(row.get("total_light_duration"))
        rem_minutes = to_int(row.get("total_rem_duration"))

        daily[snapshot_date] = {
            "sleep_total_minutes": sleep_duration,
            "light_sleep_minutes": light_minutes,
            "rem_sleep_minutes": rem_minutes,
            "sleep_session_count": 1,
        }

    print(f"Loaded sleep days: {len(daily)}")
    return daily


def merge_daily_data(*sources):
    merged = defaultdict(dict)

    for source in sources:
        for snapshot_date, values in source.items():
            merged[snapshot_date].update(values)

    return dict(merged)


def upsert_daily_snapshot(connection, snapshot_date, values):
    existing = connection.execute(
        """
        SELECT snapshot_date
        FROM daily_health_snapshots
        WHERE snapshot_date = ?
        """,
        (snapshot_date,),
    ).fetchone()

    payload = {
        "snapshot_date": snapshot_date,
        "saved_at": f"{snapshot_date}T00:00:00",
        "steps": values.get("steps"),
        "distance_meters": values.get("distance_meters"),
        "active_calories": values.get("active_calories"),
        "floors": values.get("floors"),
        "average_heart_rate": values.get("average_heart_rate"),
        "minimum_heart_rate": values.get("minimum_heart_rate"),
        "maximum_heart_rate": values.get("maximum_heart_rate"),
        "resting_heart_rate": values.get("resting_heart_rate"),
        "sleep_total_minutes": values.get("sleep_total_minutes"),
        "deep_sleep_minutes": values.get("deep_sleep_minutes"),
        "rem_sleep_minutes": values.get("rem_sleep_minutes"),
        "light_sleep_minutes": values.get("light_sleep_minutes"),
        "awake_minutes": values.get("awake_minutes"),
        "sleep_session_count": values.get("sleep_session_count"),
        "workout_session_count": values.get("workout_session_count"),
        "workout_total_duration_minutes": values.get("workout_total_duration_minutes"),
        "source_file": "samsung_historical_export",
        "imported_at": datetime.utcnow().isoformat(),
    }

    if existing:
        connection.execute(
            """
            UPDATE daily_health_snapshots
            SET
                steps = COALESCE(?, steps),
                distance_meters = COALESCE(?, distance_meters),
                active_calories = COALESCE(?, active_calories),
                floors = COALESCE(?, floors),
                average_heart_rate = COALESCE(?, average_heart_rate),
                minimum_heart_rate = COALESCE(?, minimum_heart_rate),
                maximum_heart_rate = COALESCE(?, maximum_heart_rate),
                resting_heart_rate = COALESCE(?, resting_heart_rate),
                sleep_total_minutes = COALESCE(?, sleep_total_minutes),
                deep_sleep_minutes = COALESCE(?, deep_sleep_minutes),
                rem_sleep_minutes = COALESCE(?, rem_sleep_minutes),
                light_sleep_minutes = COALESCE(?, light_sleep_minutes),
                awake_minutes = COALESCE(?, awake_minutes),
                sleep_session_count = COALESCE(?, sleep_session_count),
                workout_session_count = COALESCE(?, workout_session_count),
                workout_total_duration_minutes = COALESCE(?, workout_total_duration_minutes),
                source_file = ?,
                imported_at = ?
            WHERE snapshot_date = ?
            """,
            (
                payload["steps"],
                payload["distance_meters"],
                payload["active_calories"],
                payload["floors"],
                payload["average_heart_rate"],
                payload["minimum_heart_rate"],
                payload["maximum_heart_rate"],
                payload["resting_heart_rate"],
                payload["sleep_total_minutes"],
                payload["deep_sleep_minutes"],
                payload["rem_sleep_minutes"],
                payload["light_sleep_minutes"],
                payload["awake_minutes"],
                payload["sleep_session_count"],
                payload["workout_session_count"],
                payload["workout_total_duration_minutes"],
                payload["source_file"],
                payload["imported_at"],
                snapshot_date,
            ),
        )
    else:
        connection.execute(
            """
            INSERT INTO daily_health_snapshots (
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
                payload["snapshot_date"],
                payload["saved_at"],
                payload["steps"],
                payload["distance_meters"],
                payload["active_calories"],
                payload["floors"],
                payload["average_heart_rate"],
                payload["minimum_heart_rate"],
                payload["maximum_heart_rate"],
                payload["resting_heart_rate"],
                payload["sleep_total_minutes"],
                payload["deep_sleep_minutes"],
                payload["rem_sleep_minutes"],
                payload["light_sleep_minutes"],
                payload["awake_minutes"],
                payload["sleep_session_count"],
                payload["workout_session_count"],
                payload["workout_total_duration_minutes"],
                payload["source_file"],
                payload["imported_at"],
            ),
        )


def main():
    steps = load_steps()
    heart_rate = load_heart_rate()
    sleep = load_sleep()

    merged = merge_daily_data(steps, heart_rate, sleep)

    with sqlite3.connect(DATABASE_PATH) as connection:
        for snapshot_date, values in merged.items():
            upsert_daily_snapshot(connection, snapshot_date, values)

        connection.commit()

    print("--------------------------------")
    print(f"Samsung historical import complete.")
    print(f"Imported/updated daily snapshots: {len(merged)}")


if __name__ == "__main__":
    main()