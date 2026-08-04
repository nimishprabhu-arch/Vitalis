import sqlite3
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIR = Path("C:/Projects/Vitalis")
DATABASE_PATH = PROJECT_DIR / "database" / "vitalis.db"
OUTPUT_PATH = PROJECT_DIR / "exports" / "vitalis_history_context.md"


METRICS = [
    ("Steps", "steps"),
    ("Distance", "distance_meters"),
    ("Active calories", "active_calories"),
    ("Floors", "floors"),

    ("Average heart rate", "average_heart_rate"),
    ("Minimum heart rate", "minimum_heart_rate"),
    ("Maximum heart rate", "maximum_heart_rate"),
    ("Resting heart rate", "resting_heart_rate"),

    ("Sleep duration", "sleep_total_minutes"),
    ("Deep sleep", "deep_sleep_minutes"),
    ("REM sleep", "rem_sleep_minutes"),
    ("Light sleep", "light_sleep_minutes"),
    ("Awake time", "awake_minutes"),
    ("Sleep sessions", "sleep_session_count"),

    ("Samsung Sleep Score", "sleep_score"),
    ("Sleep efficiency", "sleep_efficiency"),
    ("Physical recovery", "physical_recovery"),
    ("Mental recovery", "mental_recovery"),

    ("Samsung Energy Score", "energy_score"),
    ("Energy sleep score", "energy_sleep_score"),
    ("Energy activity score", "energy_activity_score"),
    ("Samsung Heart Health Score", "heart_health_score"),

    ("Workout sessions", "workout_session_count"),
    ("Workout duration", "workout_total_duration_minutes"),
]


def fetch_one(cursor, query, params=()):
    return cursor.execute(query, params).fetchone()[0]


def count_metric(cursor, column_name):
    return fetch_one(
        cursor,
        f"SELECT COUNT(*) FROM daily_health_snapshots WHERE {column_name} IS NOT NULL",
    )


def avg_metric(cursor, column_name):
    return fetch_one(
        cursor,
        f"SELECT AVG({column_name}) FROM daily_health_snapshots WHERE {column_name} IS NOT NULL",
    )


def min_metric(cursor, column_name):
    return fetch_one(
        cursor,
        f"SELECT MIN({column_name}) FROM daily_health_snapshots WHERE {column_name} IS NOT NULL",
    )


def max_metric(cursor, column_name):
    return fetch_one(
        cursor,
        f"SELECT MAX({column_name}) FROM daily_health_snapshots WHERE {column_name} IS NOT NULL",
    )


def format_number(value):
    if value is None:
        return "Unavailable"

    if isinstance(value, float):
        return f"{value:.2f}"

    return str(value)


def build_metric_table(cursor):
    lines = []
    lines.append("| Metric | Days available | Average | Minimum | Maximum |")
    lines.append("|---|---:|---:|---:|---:|")

    for label, column_name in METRICS:
        days = count_metric(cursor, column_name)
        average = avg_metric(cursor, column_name)
        minimum = min_metric(cursor, column_name)
        maximum = max_metric(cursor, column_name)

        lines.append(
            f"| {label} | {days} | {format_number(average)} | {format_number(minimum)} | {format_number(maximum)} |"
        )

    return "\n".join(lines)


def build_workout_summary(cursor):
    workout_table_exists = cursor.execute(
        """
        SELECT COUNT(*)
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'workouts'
        """
    ).fetchone()[0]

    if workout_table_exists == 0:
        return "Workout history has not been imported yet."

    total_workouts = cursor.execute(
        "SELECT COUNT(*) FROM workouts"
    ).fetchone()[0]

    workout_days = cursor.execute(
        "SELECT COUNT(DISTINCT workout_date) FROM workouts"
    ).fetchone()[0]

    total_duration = cursor.execute(
        "SELECT SUM(duration_minutes) FROM workouts WHERE duration_minutes IS NOT NULL"
    ).fetchone()[0]

    total_calories = cursor.execute(
        "SELECT SUM(calories) FROM workouts WHERE calories IS NOT NULL"
    ).fetchone()[0]

    top_types = cursor.execute(
        """
        SELECT exercise_type_label, COUNT(*)
        FROM workouts
        GROUP BY exercise_type_label
        ORDER BY COUNT(*) DESC
        LIMIT 10
        """
    ).fetchall()

    lines = []
    lines.append(f"- Total workouts: {total_workouts}")
    lines.append(f"- Workout days: {workout_days}")
    lines.append(f"- Total workout duration minutes: {format_number(total_duration)}")
    lines.append(f"- Total workout calories: {format_number(total_calories)}")
    lines.append("")
    lines.append("| Workout type | Count |")
    lines.append("|---|---:|")

    for workout_type, count in top_types:
        lines.append(f"| {workout_type} | {count} |")

    return "\n".join(lines)


def build_recent_snapshots(cursor):
    rows = cursor.execute(
        """
        SELECT
            snapshot_date,
            steps,
            distance_meters,
            active_calories,
            average_heart_rate,
            minimum_heart_rate,
            maximum_heart_rate,
            resting_heart_rate,
            sleep_total_minutes,
            deep_sleep_minutes,
            rem_sleep_minutes,
            light_sleep_minutes,
            awake_minutes,
            sleep_score,
            energy_score,
            energy_sleep_score,
            energy_activity_score,
            workout_session_count,
            workout_total_duration_minutes
        FROM daily_health_snapshots
        ORDER BY snapshot_date DESC
        LIMIT 14
        """
    ).fetchall()

    lines = []
    lines.append("| Date | Steps | Sleep min | Deep | REM | Light | Awake | Sleep Score | Energy Score | Workouts | Workout min | Avg HR |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    for row in rows:
        (
            snapshot_date,
            steps,
            distance_meters,
            active_calories,
            average_heart_rate,
            minimum_heart_rate,
            maximum_heart_rate,
            resting_heart_rate,
            sleep_total_minutes,
            deep_sleep_minutes,
            rem_sleep_minutes,
            light_sleep_minutes,
            awake_minutes,
            sleep_score,
            energy_score,
            energy_sleep_score,
            energy_activity_score,
            workout_session_count,
            workout_total_duration_minutes,
        ) = row

        lines.append(
            "| "
            + " | ".join(
                [
                    str(snapshot_date),
                    format_number(steps),
                    format_number(sleep_total_minutes),
                    format_number(deep_sleep_minutes),
                    format_number(rem_sleep_minutes),
                    format_number(light_sleep_minutes),
                    format_number(awake_minutes),
                    format_number(sleep_score),
                    format_number(energy_score),
                    format_number(workout_session_count),
                    format_number(workout_total_duration_minutes),
                    format_number(average_heart_rate),
                ]
            )
            + " |"
        )

    return "\n".join(lines)


def build_context():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    first_date, latest_date, total_days = cursor.execute(
        """
        SELECT
            MIN(snapshot_date),
            MAX(snapshot_date),
            COUNT(*)
        FROM daily_health_snapshots
        """
    ).fetchone()

    generated_at = datetime.now(timezone.utc).isoformat()

    metric_table = build_metric_table(cursor)
    workout_summary = build_workout_summary(cursor)
    recent_snapshots = build_recent_snapshots(cursor)

    connection.close()

    return f"""# Vitalis Health History Context

Generated at: {generated_at}

## Dataset Coverage

- First date: {first_date}
- Latest date: {latest_date}
- Total daily snapshots: {total_days}

## Important Data Notes

- This file summarizes Samsung Health historical export data imported into Vitalis.
- Steps, distance, active calories, heart rate, sleep, sleep stages, workouts, Samsung Sleep Score, and Samsung Energy Score are imported where Samsung provided them.
- Samsung Heart Health Score currently has very limited/no usable historical values in the export.
- Resting heart rate may be limited because Samsung does not consistently expose a dedicated historical resting heart rate field in this export.
- Some Samsung app metrics may be proprietary calculations and may not appear directly in export files.

## Metric Availability

{metric_table}

## Workout History Summary

{workout_summary}

## Recent Daily Snapshots

{recent_snapshots}

## Guidance For Analysis

When answering health questions:
- Use the metric availability table to understand which metrics are reliable.
- Use workout history when analyzing fitness consistency, training load, recovery, sleep impact, and heart rate changes.
- Distinguish measured Samsung-exported values from missing or unavailable values.
- Prefer multi-week and multi-month trends over single-day conclusions.
- Do not provide medical diagnosis.
- Explain evidence clearly and mention data limitations when relevant.
"""


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    context = build_context()
    OUTPUT_PATH.write_text(context, encoding="utf-8")
    print(f"Exported Vitalis history context to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()