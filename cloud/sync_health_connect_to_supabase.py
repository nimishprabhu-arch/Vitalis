import json
import os
import sqlite3
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(
    os.environ.get(
        "HEALTH_CONNECT_DB_PATH",
        ROOT / "tmp" / "health_connect" / "health_connect_export.db",
    )
)

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "https://ltnlhxsdmcsjpcpxvvxl.supabase.co",
)
SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    "sb_publishable_U55ZW10vDw7fX-kVmWVl0w_8nXnsrOW",
)

SNAPSHOT_TABLE = "health_snapshots"
WORKOUT_TABLE = "workouts"

SNAPSHOT_COLUMNS = [
    "snapshot_date",
    "source",
    "spo2_average",
    "spo2_minimum",
    "spo2_maximum",
    "spo2_sample_count",
    "vo2_max",
    "daily_hr_average",
    "daily_hr_minimum",
    "daily_hr_maximum",
    "daily_hr_sample_count",
    "sleep_average_heart_rate",
    "sleep_minimum_heart_rate",
    "sleep_maximum_heart_rate",
    "sleep_heart_rate_sample_count",
]


def epoch_day_to_date(epoch_day):
    return (date(1970, 1, 1) + timedelta(days=int(epoch_day))).isoformat()


def ms_to_iso(ms):
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000).isoformat()


def minutes_between(start_ms, end_ms):
    if start_ms is None or end_ms is None:
        return None
    return round((end_ms - start_ms) / 1000 / 60, 2)


def exercise_label(code):
    labels = {
        4: "Other workout",
        58: "Weight training",
    }
    return labels.get(code, "Unknown")


def table_exists(connection, table_name):
    return (
        connection.execute(
            "select 1 from sqlite_master where type='table' and name=?",
            (table_name,),
        ).fetchone()
        is not None
    )


def upsert(table, rows, conflict_column, batch_size=250):
    if not rows:
        print(f"No rows to upload for {table}.")
        return 0

    uploaded = 0
    url = f"{SUPABASE_URL}/rest/v1/{table}?on_conflict={conflict_column}"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }

    for index in range(0, len(rows), batch_size):
        batch = rows[index : index + batch_size]
        request = urllib.request.Request(
            url,
            data=json.dumps(batch).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(request) as response:
                response.read()
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Supabase error {error.code} for {table}: {body}") from error

        uploaded += len(batch)
        print(f"Uploaded {table}: {uploaded}/{len(rows)}")

    return uploaded


def read_snapshot_metric_rows(connection):
    rows_by_date = {}

    def row_for(snapshot_date):
        if snapshot_date not in rows_by_date:
            rows_by_date[snapshot_date] = {
                column: None for column in SNAPSHOT_COLUMNS
            }
            rows_by_date[snapshot_date]["snapshot_date"] = snapshot_date
            rows_by_date[snapshot_date]["source"] = "health_connect_cloud_sync"

        return rows_by_date[snapshot_date]

    if table_exists(connection, "oxygen_saturation_record_table"):
        for local_date, avg_value, min_value, max_value, count_value in connection.execute(
            """
            select
                local_date,
                avg(percentage),
                min(percentage),
                max(percentage),
                count(*)
            from oxygen_saturation_record_table
            group by local_date
            """
        ):
            row = row_for(epoch_day_to_date(local_date))
            row["spo2_average"] = round(avg_value, 2) if avg_value is not None else None
            row["spo2_minimum"] = min_value
            row["spo2_maximum"] = max_value
            row["spo2_sample_count"] = count_value

    if table_exists(connection, "vo2_max_record_table"):
        for local_date, vo2_max in connection.execute(
            """
            select
                local_date,
                max(vo2_milliliters_per_minute_kilogram)
            from vo2_max_record_table
            group by local_date
            """
        ):
            row = row_for(epoch_day_to_date(local_date))
            row["vo2_max"] = round(vo2_max, 2) if vo2_max is not None else None

    if table_exists(connection, "heart_rate_record_series_table"):
        for snapshot_date, avg_hr, min_hr, max_hr, count_hr in connection.execute(
            """
            select
                date(epoch_millis / 1000, 'unixepoch', 'localtime'),
                avg(beats_per_minute),
                min(beats_per_minute),
                max(beats_per_minute),
                count(*)
            from heart_rate_record_series_table
            group by date(epoch_millis / 1000, 'unixepoch', 'localtime')
            """
        ):
            row = row_for(snapshot_date)
            row["daily_hr_average"] = round(avg_hr, 2) if avg_hr is not None else None
            row["daily_hr_minimum"] = min_hr
            row["daily_hr_maximum"] = max_hr
            row["daily_hr_sample_count"] = count_hr

    if table_exists(connection, "sleep_session_record_table") and table_exists(
        connection,
        "heart_rate_record_series_table",
    ):
        for local_date, avg_hr, min_hr, max_hr, count_hr in connection.execute(
            """
            select
                sleep.local_date,
                avg(hr.beats_per_minute),
                min(hr.beats_per_minute),
                max(hr.beats_per_minute),
                count(*)
            from sleep_session_record_table sleep
            join heart_rate_record_series_table hr
              on hr.epoch_millis between sleep.start_time and sleep.end_time
            group by sleep.local_date
            """
        ):
            row = row_for(epoch_day_to_date(local_date))
            row["sleep_average_heart_rate"] = round(avg_hr, 2) if avg_hr is not None else None
            row["sleep_minimum_heart_rate"] = min_hr
            row["sleep_maximum_heart_rate"] = max_hr
            row["sleep_heart_rate_sample_count"] = count_hr

    return list(rows_by_date.values())


def read_workout_rows(connection):
    if not table_exists(connection, "exercise_session_record_table"):
        return []

    rows = []

    for row_id, local_date, start_time, end_time, exercise_type in connection.execute(
        """
        select
            row_id,
            local_date,
            start_time,
            end_time,
            exercise_type
        from exercise_session_record_table
        order by start_time
        """
    ):
        average_hr, minimum_hr, maximum_hr = connection.execute(
            """
            select
                avg(beats_per_minute),
                min(beats_per_minute),
                max(beats_per_minute)
            from heart_rate_record_series_table
            where epoch_millis between ? and ?
            """,
            (start_time, end_time),
        ).fetchone()

        rows.append(
            {
                "workout_id": f"health_connect_{row_id}",
                "workout_date": epoch_day_to_date(local_date),
                "start_time": ms_to_iso(start_time),
                "end_time": ms_to_iso(end_time),
                "exercise_type_code": exercise_type,
                "exercise_type_label": exercise_label(exercise_type),
                "duration_minutes": minutes_between(start_time, end_time),
                "calories": None,
                "distance_meters": None,
                "average_heart_rate": round(average_hr, 2) if average_hr is not None else None,
                "minimum_heart_rate": minimum_hr,
                "maximum_heart_rate": maximum_hr,
                "source": "health_connect_cloud_sync",
                "raw_json": None,
            }
        )

    return rows


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Health Connect DB not found: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as connection:
        snapshot_rows = read_snapshot_metric_rows(connection)
        workout_rows = read_workout_rows(connection)

    print(f"Snapshot metric rows: {len(snapshot_rows)}")
    print(f"Workout rows: {len(workout_rows)}")

    upsert(SNAPSHOT_TABLE, snapshot_rows, "snapshot_date")
    upsert(WORKOUT_TABLE, workout_rows, "workout_id")

        latest_checks = [
            ("heart_rate_record_series_table", "epoch_millis"),
            ("exercise_session_record_table", "end_time"),
            ("oxygen_saturation_record_table", "time"),
            ("total_calories_burned_record_table", "end_time"),
            ("sleep_session_record_table", "end_time"),
        ]

        for table_name, column_name in latest_checks:
            try:
                latest_value = connection.execute(
                    f"select max({column_name}) from {table_name}"
                ).fetchone()[0]

                if latest_value:
                    print(f"{table_name}: {datetime.fromtimestamp(latest_value / 1000).isoformat()}")
                else:
                    print(f"{table_name}: empty")
            except Exception as error:
                print(f"{table_name}: error: {error}")

        print("Health Connect direct Supabase sync complete.")


if __name__ == "__main__":
    main()