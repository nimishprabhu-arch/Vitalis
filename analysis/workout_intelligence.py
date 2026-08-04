import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "database" / "vitalis.db"


def minutes_to_hours(minutes):
    if minutes is None:
        return "Unavailable"

    hours = int(minutes // 60)
    remaining_minutes = int(round(minutes % 60))

    if hours == 0:
        return f"{remaining_minutes}m"

    return f"{hours}h {remaining_minutes}m"


def fetch_one(cursor, query):
    return cursor.execute(query).fetchone()[0]


def print_section(title):
    print()
    print(title)
    print("-" * len(title))


def main():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    total_workouts = fetch_one(cursor, "select count(*) from workouts")
    workout_days = fetch_one(cursor, "select count(distinct workout_date) from workouts")
    total_minutes = fetch_one(cursor, "select coalesce(sum(duration_minutes), 0) from workouts")
    average_minutes = fetch_one(cursor, "select coalesce(avg(duration_minutes), 0) from workouts")
    total_calories = fetch_one(cursor, "select coalesce(sum(calories), 0) from workouts")

    print("Vitalis Workout Intelligence")
    print("--------------------------------")
    print(f"Total workouts: {total_workouts}")
    print(f"Workout days: {workout_days}")
    print(f"Total workout duration: {minutes_to_hours(total_minutes)}")
    print(f"Average workout duration: {minutes_to_hours(average_minutes)}")
    print(f"Total workout calories: {round(total_calories):,} kcal")

    print_section("Top Workout Types")
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
        limit 10
        """
    ).fetchall()

    for row in rows:
        label, count, total_type_minutes, avg_type_minutes, calories = row
        print(
            f"{label}: {count} workouts, "
            f"{minutes_to_hours(total_type_minutes)} total, "
            f"{minutes_to_hours(avg_type_minutes)} avg, "
            f"{round(calories):,} kcal"
        )

    print_section("Monthly Workout Trend")
    rows = cursor.execute(
        """
        select
            substr(workout_date, 1, 7) as month,
            count(*) as workout_count,
            count(distinct workout_date) as workout_days,
            round(coalesce(sum(duration_minutes), 0), 2) as total_minutes
        from workouts
        group by month
        order by month desc
        limit 12
        """
    ).fetchall()

    for row in rows:
        month, count, days, minutes = row
        print(f"{month}: {count} workouts across {days} days, {minutes_to_hours(minutes)}")

    print_section("Recent Workouts")
    rows = cursor.execute(
        """
        select
            workout_date,
            exercise_type_label,
            round(coalesce(duration_minutes, 0), 2),
            round(coalesce(calories, 0), 2),
            round(coalesce(distance_meters, 0), 2)
        from workouts
        order by workout_date desc, start_time desc
        limit 20
        """
    ).fetchall()

    for row in rows:
        date, label, minutes, calories, distance = row
        distance_km = distance / 1000 if distance else 0
        print(
            f"{date}: {label}, "
            f"{minutes_to_hours(minutes)}, "
            f"{round(calories):,} kcal, "
            f"{distance_km:.2f} km"
        )

    connection.close()


if __name__ == "__main__":
    main()