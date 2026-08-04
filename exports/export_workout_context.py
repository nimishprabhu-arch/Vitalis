import sqlite3
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "database" / "vitalis.db"
OUTPUT_PATH = PROJECT_ROOT / "exports" / "vitalis_workout_context.md"


def format_minutes(minutes):
    if minutes is None:
        return "Unavailable"

    hours = int(minutes // 60)
    remaining_minutes = int(round(minutes % 60))

    if hours <= 0:
        return f"{remaining_minutes}m"

    return f"{hours}h {remaining_minutes}m"


def fetch_one(cursor, query):
    return cursor.execute(query).fetchone()[0]


def build_top_workout_types(cursor):
    rows = cursor.execute(
        """
        select
            exercise_type_label,
            count(*) as workout_count,
            round(coalesce(sum(duration_minutes), 0), 2) as total_minutes,
            round(coalesce(avg(duration_minutes), 0), 2) as average_minutes,
            round(coalesce(sum(calories), 0), 2) as total_calories
        from workouts
        group by exercise_type_label
        order by workout_count desc
        limit 20
        """
    ).fetchall()

    lines = [
        "| Workout type | Count | Total duration | Average duration | Calories |",
        "|---|---:|---:|---:|---:|",
    ]

    for label, count, total_minutes, average_minutes, calories in rows:
        lines.append(
            f"| {label} | {count} | {format_minutes(total_minutes)} | "
            f"{format_minutes(average_minutes)} | {round(calories):,} kcal |"
        )

    return "\n".join(lines)


def build_monthly_trend(cursor):
    rows = cursor.execute(
        """
        select
            substr(workout_date, 1, 7) as month,
            count(*) as workout_count,
            count(distinct workout_date) as workout_days,
            round(coalesce(sum(duration_minutes), 0), 2) as total_minutes,
            round(coalesce(avg(duration_minutes), 0), 2) as average_minutes,
            round(coalesce(sum(calories), 0), 2) as total_calories
        from workouts
        group by month
        order by month desc
        limit 24
        """
    ).fetchall()

    lines = [
        "| Month | Workouts | Workout days | Total duration | Average duration | Calories |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for month, count, days, total_minutes, average_minutes, calories in rows:
        lines.append(
            f"| {month} | {count} | {days} | {format_minutes(total_minutes)} | "
            f"{format_minutes(average_minutes)} | {round(calories):,} kcal |"
        )

    return "\n".join(lines)


def build_recent_workouts(cursor):
    rows = cursor.execute(
        """
        select
            workout_date,
            exercise_type_label,
            round(coalesce(duration_minutes, 0), 2),
            round(coalesce(calories, 0), 2),
            round(coalesce(distance_meters, 0), 2),
            average_heart_rate,
            maximum_heart_rate
        from workouts
        order by workout_date desc, start_time desc
        limit 40
        """
    ).fetchall()

    lines = [
        "| Date | Type | Duration | Calories | Distance | Avg HR | Max HR |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]

    for date, label, minutes, calories, distance, average_hr, max_hr in rows:
        distance_km = distance / 1000 if distance else 0
        average_hr_text = str(round(average_hr)) if average_hr is not None else "Unavailable"
        max_hr_text = str(round(max_hr)) if max_hr is not None else "Unavailable"

        lines.append(
            f"| {date} | {label} | {format_minutes(minutes)} | "
            f"{round(calories):,} kcal | {distance_km:.2f} km | "
            f"{average_hr_text} | {max_hr_text} |"
        )

    return "\n".join(lines)


def build_context():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    total_workouts = fetch_one(cursor, "select count(*) from workouts")
    workout_days = fetch_one(cursor, "select count(distinct workout_date) from workouts")
    first_workout = fetch_one(cursor, "select min(workout_date) from workouts")
    latest_workout = fetch_one(cursor, "select max(workout_date) from workouts")
    total_minutes = fetch_one(cursor, "select coalesce(sum(duration_minutes), 0) from workouts")
    average_minutes = fetch_one(cursor, "select coalesce(avg(duration_minutes), 0) from workouts")
    total_calories = fetch_one(cursor, "select coalesce(sum(calories), 0) from workouts")

    top_workout_types = build_top_workout_types(cursor)
    monthly_trend = build_monthly_trend(cursor)
    recent_workouts = build_recent_workouts(cursor)

    connection.close()

    generated_at = datetime.now().isoformat(timespec="seconds")

    return f"""# Vitalis Workout Context

Generated at: {generated_at}

## Workout Coverage

- First workout date: {first_workout}
- Latest workout date: {latest_workout}
- Total workouts: {total_workouts}
- Workout days: {workout_days}
- Total workout duration: {format_minutes(total_minutes)}
- Average workout duration: {format_minutes(average_minutes)}
- Total workout calories: {round(total_calories):,} kcal

## Top Workout Types

{top_workout_types}

## Monthly Workout Trend

{monthly_trend}

## Recent Workouts

{recent_workouts}

## Notes for Vitalis GPT

- Use this file as the source of truth for workout history.
- Use workout history when answering questions about consistency, training load, workout habits, fitness trends, and recovery.
- Compare workout trends with sleep, heart rate, steps, and Samsung Energy Score when those files are also available.
- Treat very short "Other workout" sessions carefully; they may represent auto-detected or partial Samsung Health sessions.
- Do not claim workout history is unavailable if this file is present.
"""


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_context(), encoding="utf-8")
    print(f"Exported Vitalis workout context to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()