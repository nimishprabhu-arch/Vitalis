import json
import sqlite3
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VITALIS_DB = ROOT / "database" / "vitalis.db"
HEALTH_CONNECT_DB = Path(
    os.environ.get(
        "HEALTH_CONNECT_DB_PATH",
        r"C:\Users\nimis\Downloads\Health Connect\health_connect_export.db",
    )
)


EXERCISE_TYPE_LABELS = {
    4: "Other workout",
    58: "Weight training",
}


def millis_to_iso(epoch_millis):
    if epoch_millis is None:
        return None
    return datetime.fromtimestamp(epoch_millis / 1000).isoformat()


def millis_to_date(epoch_millis):
    if epoch_millis is None:
        return None
    return datetime.fromtimestamp(epoch_millis / 1000).date().isoformat()


def ensure_workouts_table(connection):
    connection.execute(
        """
        create table if not exists workouts (
            workout_id text primary key,
            workout_date text,
            start_time text,
            end_time text,
            exercise_type_code integer,
            exercise_type_label text,
            duration_minutes real,
            calories real,
            distance_meters real,
            average_heart_rate real,
            minimum_heart_rate real,
            maximum_heart_rate real,
            source text,
            raw_json text,
            imported_at text
        )
        """
    )


def get_hr_rollup(health_connection, start_time, end_time):
    row = health_connection.execute(
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

    if not row:
        return None, None, None

    average_hr, minimum_hr, maximum_hr = row
    return (
        round(average_hr, 2) if average_hr is not None else None,
        minimum_hr,
        maximum_hr,
    )


def import_workouts():
    imported_at = datetime.now(timezone.utc).isoformat()
    updated = 0

    with sqlite3.connect(VITALIS_DB) as vitalis_connection:
        vitalis_connection.row_factory = sqlite3.Row
        ensure_workouts_table(vitalis_connection)

        with sqlite3.connect(HEALTH_CONNECT_DB) as health_connection:
            health_connection.row_factory = sqlite3.Row

            rows = health_connection.execute(
                """
                select
                    row_id,
                    start_time,
                    end_time,
                    local_date,
                    exercise_type,
                    title,
                    has_route
                from exercise_session_record_table
                order by start_time asc
                """
            ).fetchall()

            for row in rows:
                start_time = row["start_time"]
                end_time = row["end_time"]

                if not start_time or not end_time:
                    continue

                duration_minutes = round((end_time - start_time) / 60000, 2)
                workout_date = millis_to_date(start_time)
                exercise_type_code = row["exercise_type"]
                exercise_type_label = (
                    EXERCISE_TYPE_LABELS.get(exercise_type_code)
                    or row["title"]
                    or f"Exercise type {exercise_type_code}"
                )

                average_hr, minimum_hr, maximum_hr = get_hr_rollup(
                    health_connection,
                    start_time,
                    end_time,
                )

                workout_id = f"health_connect_{row['row_id']}"

                raw_json = json.dumps(
                    {
                        "row_id": row["row_id"],
                        "local_date": row["local_date"],
                        "exercise_type": exercise_type_code,
                        "title": row["title"],
                        "has_route": row["has_route"],
                    },
                    ensure_ascii=False,
                )

                cursor = vitalis_connection.execute(
                    """
                    insert into workouts (
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
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    on conflict(workout_id)
                    do update set
                        workout_date = excluded.workout_date,
                        start_time = excluded.start_time,
                        end_time = excluded.end_time,
                        exercise_type_code = excluded.exercise_type_code,
                        exercise_type_label = excluded.exercise_type_label,
                        duration_minutes = excluded.duration_minutes,
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
                        millis_to_iso(start_time),
                        millis_to_iso(end_time),
                        exercise_type_code,
                        exercise_type_label,
                        duration_minutes,
                        None,
                        None,
                        average_hr,
                        minimum_hr,
                        maximum_hr,
                        "health_connect_export",
                        raw_json,
                        imported_at,
                    ),
                )

                updated += cursor.rowcount

        vitalis_connection.commit()

    print("Health Connect workout import complete.")
    print(f"Imported/updated workouts: {updated}")


if __name__ == "__main__":
    import_workouts()