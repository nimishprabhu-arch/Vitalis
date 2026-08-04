import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "database" / "vitalis.db"
OUTPUT_PATH = PROJECT_ROOT / "exports" / "vitalis_workout_trends_context.md"


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def format_minutes(minutes):
    if minutes is None:
        return "Unavailable"

    hours = int(minutes // 60)
    remaining_minutes = int(round(minutes % 60))

    if hours <= 0:
        return f"{remaining_minutes}m"

    return f"{hours}h {remaining_minutes}m"


def fetch_workout_days(cursor):
    rows = cursor.execute(
        """
        select distinct workout_date
        from workouts
        where workout_date is not null
        order by workout_date
        """
    ).fetchall()

    return {parse_date(row[0]) for row in rows}


def calculate_current_streak(workout_days, latest_date):
    if not workout_days or latest_date is None:
        return 0

    streak = 0
    current_day = latest_date

    while current_day in workout_days:
        streak += 1
        current_day -= timedelta(days=1)

    return streak


def calculate_longest_streak(workout_days):
    if not workout_days:
        return 0

    longest = 0
    current = 0
    previous_day = None

    for workout_day in sorted(workout_days):
        if previous_day is None or workout_day == previous_day + timedelta(days=1):
            current += 1
        else:
            current = 1

        longest = max(longest, current)
        previous_day = workout_day

    return longest


def build_period_summary(cursor, latest_date, days):
    start_date = latest_date - timedelta(days=days - 1)

    row = cursor.execute(
        """
        select
            count(*) as workouts,
            count(distinct workout_date) as workout_days,
            round(coalesce(sum(duration_minutes), 0), 2) as total_minutes,
            round(coalesce(avg(duration_minutes), 0), 2) as average_minutes,
            round(coalesce(sum(calories), 0), 2) as calories
        from workouts
        where workout_date between ? and ?
        """,
        (start_date.isoformat(), latest_date.isoformat()),
    ).fetchone()

    workouts, workout_days, total_minutes, average_minutes, calories = row
    consistency_percent = round((workout_days / days) * 100, 1)

    return {
        "days": days,
        "start_date": start_date,
        "end_date": latest_date,
        "workouts": workouts,
        "workout_days": workout_days,
        "consistency_percent": consistency_percent,
        "total_minutes": total_minutes,
        "average_minutes": average_minutes,
        "calories": calories,
    }


def build_consistency_table(cursor, latest_date):
    rows = [
        build_period_summary(cursor, latest_date, 30),
        build_period_summary(cursor, latest_date, 90),
        build_period_summary(cursor, latest_date, 365),
    ]

    lines = [
        "| Period | Workout days | Workouts | Consistency | Total duration | Calories |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for row in rows:
        lines.append(
            f"| Last {row['days']} days | {row['workout_days']} | {row['workouts']} | "
            f"{row['consistency_percent']}% | {format_minutes(row['total_minutes'])} | "
            f"{round(row['calories']):,} kcal |"
        )

    return "\n".join(lines)


def build_best_months_table(cursor):
    rows = cursor.execute(
        """
        select
            substr(workout_date, 1, 7) as month,
            count(*) as workouts,
            count(distinct workout_date) as workout_days,
            round(coalesce(sum(duration_minutes), 0), 2) as total_minutes,
            round(coalesce(sum(calories), 0), 2) as calories
        from workouts
        group by month
        order by workout_days desc, workouts desc
        limit 12
        """
    ).fetchall()

    lines = [
        "| Month | Workout days | Workouts | Total duration | Calories |",
        "|---|---:|---:|---:|---:|",
    ]

    for month, workouts, workout_days, total_minutes, calories in rows:
        lines.append(
            f"| {month} | {workout_days} | {workouts} | "
            f"{format_minutes(total_minutes)} | {round(calories):,} kcal |"
        )

    return "\n".join(lines)


def build_training_load_table(cursor, latest_date):
    lines = [
        "| Period | Workouts | Workout days | Total duration | Calories |",
        "|---|---:|---:|---:|---:|",
    ]

    for days in [7, 14, 30]:
        start_date = latest_date - timedelta(days=days - 1)

        row = cursor.execute(
            """
            select
                count(*) as workouts,
                count(distinct workout_date) as workout_days,
                round(coalesce(sum(duration_minutes), 0), 2) as total_minutes,
                round(coalesce(sum(calories), 0), 2) as calories
            from workouts
            where workout_date between ? and ?
            """,
            (start_date.isoformat(), latest_date.isoformat()),
        ).fetchone()

        workouts, workout_days, total_minutes, calories = row

        lines.append(
            f"| Last {days} days | {workouts} | {workout_days} | "
            f"{format_minutes(total_minutes)} | {round(calories):,} kcal |"
        )

    return "\n".join(lines)


def build_context():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    latest_date_text = cursor.execute("select max(workout_date) from workouts").fetchone()[0]
    if latest_date_text is None:
        connection.close()
        return "# Vitalis Workout Trends Context\n\nNo workout data found.\n"

    latest_date = parse_date(latest_date_text)
    workout_days = fetch_workout_days(cursor)

    current_streak = calculate_current_streak(workout_days, latest_date)
    longest_streak = calculate_longest_streak(workout_days)
    consistency_table = build_consistency_table(cursor, latest_date)
    best_months_table = build_best_months_table(cursor)
    training_load_table = build_training_load_table(cursor, latest_date)

    connection.close()

    generated_at = datetime.now().isoformat(timespec="seconds")

    return f"""# Vitalis Workout Trends Context

Generated at: {generated_at}

## Workout Trend Summary

- Latest workout date: {latest_date}
- Current workout streak: {current_streak} days
- Longest workout streak: {longest_streak} days

## Workout Consistency

{consistency_table}

## Best Workout Months

{best_months_table}

## Training Load Windows

{training_load_table}

## Notes for Vitalis GPT

- Use this file to answer questions about workout consistency, streaks, and training load.
- Treat workout frequency and total duration as stronger training-load signals than workout count alone.
- Compare high training-load periods with sleep duration, sleep score, resting heart rate, average heart rate, and Samsung Energy Score when available.
- If the user asks whether they are consistent, use the 30/90/365 day consistency windows.
- If the user asks whether they may be overtraining, compare recent 7/14/30 day training load with sleep and heart-rate recovery data.
"""


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_context(), encoding="utf-8")
    print(f"Exported Vitalis workout trends context to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()