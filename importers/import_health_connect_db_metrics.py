import sqlite3
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VITALIS_DB = ROOT / "database" / "vitalis.db"
HEALTH_CONNECT_DB = Path(r"C:\Users\nimis\Downloads\Health Connect\health_connect_export.db")


def epoch_day_to_date(epoch_day):
    return (date(1970, 1, 1) + timedelta(days=int(epoch_day))).isoformat()


def ensure_columns(connection):
    existing = {
        row[1]
        for row in connection.execute("pragma table_info(daily_health_snapshots)")
    }

    columns = {
        "spo2_average": "real",
        "spo2_minimum": "real",
        "spo2_maximum": "real",
        "spo2_sample_count": "integer",
        "vo2_max": "real",
    }

    for column, column_type in columns.items():
        if column not in existing:
            connection.execute(
                f"alter table daily_health_snapshots add column {column} {column_type}"
            )


def import_spo2(vitalis_connection, health_connection):
    rows = health_connection.execute(
        """
        select
            local_date,
            count(*) as sample_count,
            avg(percentage) as average_spo2,
            min(percentage) as minimum_spo2,
            max(percentage) as maximum_spo2
        from oxygen_saturation_record_table
        group by local_date
        """
    ).fetchall()

    updated = 0

    for local_date, sample_count, average_spo2, minimum_spo2, maximum_spo2 in rows:
        snapshot_date = epoch_day_to_date(local_date)

        cursor = vitalis_connection.execute(
            """
            update daily_health_snapshots
            set
                spo2_average = ?,
                spo2_minimum = ?,
                spo2_maximum = ?,
                spo2_sample_count = ?
            where snapshot_date = ?
            """,
            (
                round(average_spo2, 2) if average_spo2 is not None else None,
                minimum_spo2,
                maximum_spo2,
                sample_count,
                snapshot_date,
            ),
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
        snapshot_date = epoch_day_to_date(local_date)

        cursor = vitalis_connection.execute(
            """
            update daily_health_snapshots
            set vo2_max = ?
            where snapshot_date = ?
            """,
            (
                round(vo2_max, 2) if vo2_max is not None else None,
                snapshot_date,
            ),
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

            vitalis_connection.commit()

    print("Health Connect DB metrics import complete.")
    print(f"SpO2 rows updated: {spo2_updated}")
    print(f"VO2 max rows updated: {vo2_updated}")


if __name__ == "__main__":
    main()