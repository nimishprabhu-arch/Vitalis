import sqlite3
from pathlib import Path

PROJECT_DIR = Path("C:/Projects/Vitalis")
DATABASE_PATH = PROJECT_DIR / "database" / "vitalis.db"


def format_minutes(value):
    if value is None:
        return "Unavailable"

    hours = value // 60
    minutes = value % 60
    return f"{hours}h {minutes}m"


def main():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row

        row = connection.execute(
            """
            SELECT *
            FROM daily_health_snapshots
            ORDER BY snapshot_date DESC
            LIMIT 1
            """
        ).fetchone()

    if row is None:
        print("No health snapshots found.")
        return

    print("Vitalis latest health snapshot")
    print("--------------------------------")
    print(f"Date: {row['snapshot_date']}")
    print(f"Saved at: {row['saved_at']}")
    print()
    print(f"Steps: {row['steps']}")
    print(f"Distance: {row['distance_meters']} meters")
    print(f"Active calories: {row['active_calories']}")
    print(f"Floors: {row['floors']}")
    print()
    print(f"Average heart rate: {row['average_heart_rate']}")
    print(f"Minimum heart rate: {row['minimum_heart_rate']}")
    print(f"Maximum heart rate: {row['maximum_heart_rate']}")
    print(f"Resting heart rate: {row['resting_heart_rate']}")
    print()
    print(f"Sleep total: {format_minutes(row['sleep_total_minutes'])}")
    print(f"Deep sleep: {format_minutes(row['deep_sleep_minutes'])}")
    print(f"REM sleep: {format_minutes(row['rem_sleep_minutes'])}")
    print(f"Light sleep: {format_minutes(row['light_sleep_minutes'])}")
    print(f"Awake: {format_minutes(row['awake_minutes'])}")
    print()
    print(f"Workout sessions: {row['workout_session_count']}")
    print(f"Workout duration: {format_minutes(row['workout_total_duration_minutes'])}")


if __name__ == "__main__":
    main()