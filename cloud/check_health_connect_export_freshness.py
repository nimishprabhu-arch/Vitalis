import os
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(
    os.environ.get(
        "HEALTH_CONNECT_DB_PATH",
        ROOT / "tmp" / "health_connect" / "health_connect_export.db",
    )
)

CHECKS = [
    ("heart_rate_record_series_table", "epoch_millis"),
    ("exercise_session_record_table", "end_time"),
    ("oxygen_saturation_record_table", "time"),
    ("total_calories_burned_record_table", "end_time"),
    ("sleep_session_record_table", "end_time"),
]


def table_exists(connection, table_name):
    return (
        connection.execute(
            "select 1 from sqlite_master where type='table' and name=?",
            (table_name,),
        ).fetchone()
        is not None
    )


def format_epoch_ms(value):
    if value is None:
        return "empty"

    return datetime.fromtimestamp(value / 1000).isoformat()


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Health Connect DB not found: {DB_PATH}")

    print(f"Health Connect DB: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as connection:
        for table_name, column_name in CHECKS:
            if not table_exists(connection, table_name):
                print(f"{table_name}: missing")
                continue

            latest_value = connection.execute(
                f"select max({column_name}) from {table_name}"
            ).fetchone()[0]

            print(f"{table_name}: {format_epoch_ms(latest_value)}")


if __name__ == "__main__":
    main()