import sqlite3
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VITALIS_DB = ROOT / "database" / "vitalis.db"
HEALTH_CONNECT_DB = Path(r"C:\Users\nimis\Downloads\Health Connect\health_connect_export.db")


def epoch_day_to_date(epoch_day):
    return (date(1970, 1, 1) + timedelta(days=int(epoch_day))).isoformat()


def ensure_columns(connection):
    existing = {row[1] for row in connection.execute("pragma table_info(daily_health_snapshots)")}

    columns = {
        "spo2_average": "real",
        "spo2_minimum": "real",
        "spo2_maximum": "real",
        "spo2_sample_count": "integer",
        "vo2_max": "real",
        "sleep_average_heart_rate": "real",
        "sleep_minimum_heart_rate": "real",
        "sleep_maximum_heart_rate": "real",
        "sleep_heart_rate_sample_count": "integer",
        "daily_hr_average": "real",
        "daily_hr_minimum": "real",
        "daily_hr_maximum": "real",
        "daily_hr_sample_count": "integer",
    }

    for column, column_type in columns.items():
        if column not in existing:
            connection.execute(f"alter table daily_health_snapshots add column {column} {column_type}")


def import_spo2(vitalis_connection, health_connection):
    rows = health_connection.execute(
        """
        select local_date, count(*), avg(percentage), min(percentage), max(percentage)
        from oxygen_saturation_record_table
        group by local_date
        """
    ).fetchall()

    updated = 0
    for local_date, sample_count, average_spo2, minimum_spo2, maximum_spo2 in rows:
        cursor = vitalis_connection.execute(
            """
            update daily_health_snapshots
            set spo2_average = ?, spo2_minimum = ?, spo2_maximum = ?, spo2_sample_count = ?
            where snapshot_date = ?
            """,
            (round(average_spo2, 2), minimum_spo2, maximum_spo2, sample_count, epoch_day_to_date(local_date)),
        )
        updated += cursor.rowcount

    return updated


def import_vo2_max(vitalis_connection, health_connection):
    rows = health_connection.execute(
        """
        select local_date, vo2_milliliters_per_minute_kilogram
        from vo2_max_record_table
        """
    ).fetchall()

    updated = 0
    for local_date, vo2_max in rows:
        cursor = vitalis_connection.execute(
            """
            update daily_health_snapshots
            set vo2_max = ?
            where snapshot_date = ?
            """,
            (round(vo2_max, 2), epoch_day_to_date(local_date)),
        )
        updated += cursor.rowcount

    return updated


def import_sleep_hr(vitalis_connection, health_connection):
    rows = health_connection.execute(
        """
        select
            s.local_date,
            avg(h.beats_per_minute),
            min(h.beats_per_minute),
            max(h.beats_per_minute),
            count(*)
        from sleep_session_record_table s
        join heart_rate_record_series_table h
          on h.epoch_millis between s.start_time and s.end_time
        group by s.local_date
        """
    ).fetchall()

    updated = 0
    for local_date, average_hr, minimum_hr, maximum_hr, sample_count in rows:
        cursor = vitalis_connection.execute(
            """
            update daily_health_snapshots
            set
                sleep_average_heart_rate = ?,
                sleep_minimum_heart_rate = ?,
                sleep_maximum_heart_rate = ?,
                sleep_heart_rate_sample_count = ?
            where snapshot_date = ?
            """,
            (round(average_hr, 2), minimum_hr, maximum_hr, sample_count, epoch_day_to_date(local_date)),
        )
        updated += cursor.rowcount

    return updated


def import_daily_hr(vitalis_connection, health_connection):
    rows = health_connection.execute(
        """
        select
            date(epoch_millis / 1000, 'unixepoch', 'localtime'),
            avg(beats_per_minute),
            min(beats_per_minute),
            max(beats_per_minute),
            count(*)
        from heart_rate_record_series_table
        group by 1
        """
    ).fetchall()

    updated = 0
    for snapshot_date, average_hr, minimum_hr, maximum_hr, sample_count in rows:
        if not snapshot_date:
            continue

        cursor = vitalis_connection.execute(
            """
            update daily_health_snapshots
            set
                daily_hr_average = ?,
                daily_hr_minimum = ?,
                daily_hr_maximum = ?,
                daily_hr_sample_count = ?
            where snapshot_date = ?
            """,
            (round(average_hr, 2), minimum_hr, maximum_hr, sample_count, snapshot_date),
        )
        updated += cursor.rowcount

    return updated


def main():
    if not HEALTH_CONNECT_DB.exists():
        raise FileNotFoundError(f"Health Connect DB not found: {HEALTH_CONNECT_DB}")

    with sqlite3.connect(VITALIS_DB) as vitalis_connection:
        with sqlite3.connect(HEALTH_CONNECT_DB) as health_connection:
            ensure_columns(vitalis_connection)

            spo2_updated = import_spo2(vitalis_connection, health_connection)
            vo2_updated = import_vo2_max(vitalis_connection, health_connection)
            sleep_hr_updated = import_sleep_hr(vitalis_connection, health_connection)
            daily_hr_updated = import_daily_hr(vitalis_connection, health_connection)

            vitalis_connection.commit()

    print("Health Connect DB metrics import complete.")
    print(f"SpO2 rows updated: {spo2_updated}")
    print(f"VO2 max rows updated: {vo2_updated}")
    print(f"Sleep HR rows updated: {sleep_hr_updated}")
    print(f"Daily HR rows updated: {daily_hr_updated}")


if __name__ == "__main__":
    main()