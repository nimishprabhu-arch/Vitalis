import csv
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "database" / "vitalis.db"

SAMSUNG_EXPORT_FOLDER = Path(
    r"C:\Users\nimis\health-data\samsung-export\samsunghealth_nimish.prabhu_20260725150269"
)

CALORIE_FILE_PATTERN = "*calories_burned.details*.csv"


def clean_float(value):
    value = (value or "").strip()
    if not value:
        return None

    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def parse_day(value):
    value = (value or "").strip()
    if not value:
        return None

    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass

    return None


def find_latest_calorie_file():
    files = list(SAMSUNG_EXPORT_FOLDER.rglob(CALORIE_FILE_PATTERN))

    if not files:
        raise FileNotFoundError(
            f"No Samsung calorie CSV found under: {SAMSUNG_EXPORT_FOLDER}"
        )

    return max(files, key=lambda path: path.stat().st_mtime)


def ensure_columns(connection):
    existing = {
        row[1]
        for row in connection.execute("pragma table_info(daily_health_snapshots)")
    }

    columns = {
        "active_time_minutes": "real",
        "rest_calories": "real",
        "exercise_calories": "real",
        "total_burned_calories": "real",
    }

    for column, column_type in columns.items():
        if column not in existing:
            connection.execute(
                f"alter table daily_health_snapshots add column {column} {column_type}"
            )


def import_calories():
    calorie_file = find_latest_calorie_file()
    updated = 0
    skipped = 0

    with sqlite3.connect(DATABASE_PATH) as connection:
        ensure_columns(connection)

        with calorie_file.open("r", encoding="utf-8-sig", newline="") as file:
            preamble = file.readline()
            reader = csv.DictReader(file)

            for row in reader:
                snapshot_date = parse_day(
                    row.get("com.samsung.shealth.calories_burned.day_time")
                )

                if not snapshot_date:
                    skipped += 1
                    continue

                active_calories = clean_float(
                    row.get("com.samsung.shealth.calories_burned.active_calorie")
                )
                rest_calories = clean_float(
                    row.get("com.samsung.shealth.calories_burned.rest_calorie")
                )
                tef_calories = clean_float(
                    row.get("com.samsung.shealth.calories_burned.tef_calorie")
                )
                exercise_calories = clean_float(row.get("total_exercise_calories"))
                active_time_millis = clean_float(
                    row.get("com.samsung.shealth.calories_burned.active_time")
                )

                active_time_minutes = (
                    round(active_time_millis / 60000, 2)
                    if active_time_millis is not None
                    else None
                )

                total_burned_calories = None
                if rest_calories is not None or active_calories is not None or tef_calories is not None:
                    total_burned_calories = round(
                        (rest_calories or 0) + (active_calories or 0) + (tef_calories or 0),
                        2,
                    )

                cursor = connection.execute(
                    """
                    update daily_health_snapshots
                    set
                        active_calories = coalesce(?, active_calories),
                        active_time_minutes = coalesce(?, active_time_minutes),
                        rest_calories = coalesce(?, rest_calories),
                        exercise_calories = coalesce(?, exercise_calories),
                        total_burned_calories = coalesce(?, total_burned_calories)
                    where snapshot_date = ?
                    """,
                    (
                        active_calories,
                        active_time_minutes,
                        rest_calories,
                        exercise_calories,
                        total_burned_calories,
                        snapshot_date,
                    ),
                )

                if cursor.rowcount:
                    updated += cursor.rowcount
                else:
                    skipped += 1

        connection.commit()

    print("Samsung calorie import complete.")
    print(f"Source file: {calorie_file}")
    print(f"Updated snapshot rows: {updated}")
    print(f"Skipped rows: {skipped}")


if __name__ == "__main__":
    import_calories()