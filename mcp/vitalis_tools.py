import sqlite3
from pathlib import Path

PROJECT_DIR = Path("C:/Projects/Vitalis")
DATABASE_PATH = PROJECT_DIR / "database" / "vitalis.db"


def format_minutes(value):
    if value is None:
        return "Unavailable"

    hours = int(value) // 60
    minutes = int(value) % 60
    return f"{hours}h {minutes}m"


def get_latest_health_snapshot():
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
        return "No health snapshots found."

    return {
        "date": row["snapshot_date"],
        "saved_at": row["saved_at"],

        "activity": {
            "steps": row["steps"],
            "distance_meters": row["distance_meters"],
            "active_calories": row["active_calories"],
            "floors": row["floors"],
        },

        "heart_rate": {
            "average": row["average_heart_rate"],
            "minimum": row["minimum_heart_rate"],
            "maximum": row["maximum_heart_rate"],
            "resting": row["resting_heart_rate"],
        },

        "sleep": {
            "total": format_minutes(row["sleep_total_minutes"]),
            "deep": format_minutes(row["deep_sleep_minutes"]),
            "rem": format_minutes(row["rem_sleep_minutes"]),
            "light": format_minutes(row["light_sleep_minutes"]),
            "awake": format_minutes(row["awake_minutes"]),
            "sessions": row["sleep_session_count"],
        },

        "workouts": {
            "sessions": row["workout_session_count"],
            "total_duration": format_minutes(row["workout_total_duration_minutes"]),
        },
    }


def summarize_latest_health_snapshot():
    snapshot = get_latest_health_snapshot()

    if isinstance(snapshot, str):
        return snapshot

    return f"""
Vitalis latest health snapshot

Date: {snapshot["date"]}
Saved at: {snapshot["saved_at"]}

Activity:
- Steps: {snapshot["activity"]["steps"]}
- Distance: {snapshot["activity"]["distance_meters"]} meters
- Active calories: {snapshot["activity"]["active_calories"]}
- Floors: {snapshot["activity"]["floors"]}

Heart rate:
- Average: {snapshot["heart_rate"]["average"]}
- Minimum: {snapshot["heart_rate"]["minimum"]}
- Maximum: {snapshot["heart_rate"]["maximum"]}
- Resting: {snapshot["heart_rate"]["resting"]}

Sleep:
- Total: {snapshot["sleep"]["total"]}
- Deep: {snapshot["sleep"]["deep"]}
- REM: {snapshot["sleep"]["rem"]}
- Light: {snapshot["sleep"]["light"]}
- Awake: {snapshot["sleep"]["awake"]}
- Sessions: {snapshot["sleep"]["sessions"]}

Workouts:
- Sessions: {snapshot["workouts"]["sessions"]}
- Total duration: {snapshot["workouts"]["total_duration"]}
""".strip()


if __name__ == "__main__":
    print(summarize_latest_health_snapshot())