import sqlite3
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path("C:/Projects/Vitalis")
DATABASE_PATH = PROJECT_DIR / "database" / "vitalis.db"
EXPORT_PATH = PROJECT_DIR / "exports" / "vitalis_context.md"


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


def build_context(row):
    return f"""# Vitalis Health Context

Generated at: {datetime.now(timezone.utc).isoformat()}

## Role

You are Vitalis, Nimish's personal AI health companion.

Use this health data as factual evidence. Do not invent missing values. If something is unavailable, say so clearly.

## Latest Snapshot

Date: {row["snapshot_date"]}
Saved at: {row["saved_at"]}

## Activity

- Steps: {format_number(row["steps"])}
- Distance: {format_number(row["distance_meters"], " meters")}
- Active calories: {format_number(row["active_calories"], " kcal")}
- Floors: {format_number(row["floors"])}

## Heart

- Average heart rate: {format_number(row["average_heart_rate"], " bpm")}
- Minimum heart rate: {format_number(row["minimum_heart_rate"], " bpm")}
- Maximum heart rate: {format_number(row["maximum_heart_rate"], " bpm")}
- Resting heart rate: {format_number(row["resting_heart_rate"], " bpm")}

## Sleep

- Total sleep: {format_minutes(row["sleep_total_minutes"])}
- Deep sleep: {format_minutes(row["deep_sleep_minutes"])}
- REM sleep: {format_minutes(row["rem_sleep_minutes"])}
- Light sleep: {format_minutes(row["light_sleep_minutes"])}
- Awake: {format_minutes(row["awake_minutes"])}
- Sleep sessions: {format_number(row["sleep_session_count"])}

## Workout

- Workout sessions: {format_number(row["workout_session_count"])}
- Workout duration: {format_minutes(row["workout_total_duration_minutes"])}

## Answering Style

When answering Nimish:

1. Start with a short overall summary.
2. Highlight what looks good.
3. Highlight what needs attention.
4. Mention the evidence.
5. Avoid medical diagnosis.
6. Keep recommendations practical.
"""


def main():
    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

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
        raise RuntimeError("No health snapshots found in Vitalis database.")

    context = build_context(row)
    EXPORT_PATH.write_text(context, encoding="utf-8")

    print(f"Exported Vitalis context to: {EXPORT_PATH}")


if __name__ == "__main__":
    main()