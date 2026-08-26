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

MAX_ALLOWED_DAYS_BEHIND = 3
REQUIRED_TABLES = {
    "heart_rate_record_series_table",
    "exercise_session_record_table",
    "total_calories_burned_record_table",
}

def log(message):
    print(message, flush=True)


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

    log(f"Health Connect DB: {DB_PATH}")

    now = datetime.now()
    stale_required_tables = []

    with sqlite3.connect(DB_PATH) as connection:
        for table_name, column_name in CHECKS:
            if not table_exists(connection, table_name):
                log(f"{table_name}: missing")
                if table_name in REQUIRED_TABLES:
                    stale_required_tables.append(f"{table_name}: missing")
                continue

            latest_value = connection.execute(
                f"select max({column_name}) from {table_name}"
            ).fetchone()[0]

            latest_text = format_epoch_ms(latest_value)
            log(f"{table_name}: {latest_text}")

            if table_name in REQUIRED_TABLES and latest_value is not None:
                latest_date = datetime.fromtimestamp(latest_value / 1000).date()
                days_behind = (now.date() - latest_date).days

                if days_behind > MAX_ALLOWED_DAYS_BEHIND:
                    stale_required_tables.append(
                        f"{table_name}: {days_behind} days behind"
                    )

    if stale_required_tables:
        raise RuntimeError(
            "Health Connect export is stale for required tables: "
            + "; ".join(stale_required_tables)
        )