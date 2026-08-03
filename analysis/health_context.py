import sqlite3
from pathlib import Path

PROJECT_DIR = Path("C:/Projects/Vitalis")
DATABASE_PATH = PROJECT_DIR / "database" / "vitalis.db"


def format_minutes(value):
    if value is None:
        return "Unavailable"

    value = int(value)
    hours = value // 60
    minutes = value % 60
    return f"{hours}h {minutes}m"


def format_number(value, suffix=""):
    if value is None:
        return "Unavailable"

    if isinstance(value, float):
        value = round(value, 2)

    return f"{value}{suffix}"


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
        print("No Vitalis health data found yet.")
        return

    context = f"""
You are Vitalis, Nimish's personal AI health companion.

Use the following latest health snapshot as factual evidence.
Do not invent missing data. If a value is unavailable, say so clearly.

Latest snapshot:
- Date: {row["snapshot_date"]}
- Saved at: {row["saved_at"]}

Activity:
- Steps: {format_number(row["steps"])}
- Distance: {format_number(row["distance_meters"], " meters")}
- Active calories: {format_number(row["active_calories"], " kcal")}
- Floors: {format_number(row["floors"])}

Heart:
- Average heart rate: {format_number(row["average_heart_rate"], " bpm")}
- Minimum heart rate: {format_number(row["minimum_heart_rate"], " bpm")}
- Maximum heart rate: {format_number(row["maximum_heart_rate"], " bpm")}
- Resting heart rate: {format_number(row["resting_heart_rate"], " bpm")}

Sleep:
- Total sleep: {format_minutes(row["sleep_total_minutes"])}
- Deep sleep: {format_minutes(row["deep_sleep_minutes"])}
- REM sleep: {format_minutes(row["rem_sleep_minutes"])}
- Light sleep: {format_minutes(row["light_sleep_minutes"])}
- Awake: {format_minutes(row["awake_minutes"])}
- Sleep sessions: {format_number(row["sleep_session_count"])}

Workout:
- Workout sessions: {format_number(row["workout_session_count"])}
- Workout duration: {format_minutes(row["workout_total_duration_minutes"])}

Suggested answer style:
- Start with a short overall summary.
- Highlight what looks good.
- Highlight what needs attention.
- Mention evidence from the data.
- Avoid medical diagnosis.
""".strip()

    print(context)


if __name__ == "__main__":
    main()