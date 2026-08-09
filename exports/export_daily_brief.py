import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "database" / "vitalis.db"
OUTPUT_PATH = PROJECT_ROOT / "exports" / "vitalis_daily_brief.md"


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


def format_number(value, suffix="", decimals=1):
    if value is None:
        return "Unavailable"

    return f"{round(value, decimals)}{suffix}"


def get_latest_snapshot(cursor):
    return cursor.execute(
        """
        select
            snapshot_date,
            steps,
            distance_meters,
            active_calories,
            average_heart_rate,
            resting_heart_rate,
            sleep_total_minutes,
            deep_sleep_minutes,
            rem_sleep_minutes,
            light_sleep_minutes,
            awake_minutes,
            sleep_score,
            energy_score,
            energy_sleep_score,
            energy_activity_score
        from daily_health_snapshots
        order by snapshot_date desc
        limit 1
        """
    ).fetchone()


def get_workout_summary(cursor, snapshot_date):
    return cursor.execute(
        """
        select
            count(*) as workouts,
            round(coalesce(sum(duration_minutes), 0), 2) as workout_minutes,
            round(coalesce(sum(calories), 0), 2) as workout_calories
        from workouts
        where workout_date = ?
        """,
        (snapshot_date,),
    ).fetchone()


def get_streak(cursor, latest_date):
    rows = cursor.execute(
        """
        select distinct workout_date
        from workouts
        where workout_date is not null
        """
    ).fetchall()

    workout_days = {parse_date(row[0]) for row in rows}

    streak = 0
    current_day = latest_date

    while current_day in workout_days:
        streak += 1
        current_day -= timedelta(days=1)

    return streak


def get_30_day_consistency(cursor, latest_date):
    start_date = latest_date - timedelta(days=29)

    row = cursor.execute(
        """
        select
            count(*) as workouts,
            count(distinct workout_date) as workout_days,
            round(coalesce(sum(duration_minutes), 0), 2) as workout_minutes
        from workouts
        where workout_date between ? and ?
        """,
        (start_date.isoformat(), latest_date.isoformat()),
    ).fetchone()

    workouts, workout_days, workout_minutes = row
    consistency = round((workout_days / 30) * 100, 1)

    return {
        "workouts": workouts,
        "workout_days": workout_days,
        "workout_minutes": workout_minutes,
        "consistency": consistency,
    }


def get_recovery_note(snapshot, workout_summary, consistency):
    (
        snapshot_date,
        steps,
        distance_meters,
        active_calories,
        average_heart_rate,
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
    ) = snapshot

    workout_minutes = workout_summary[1] or 0
    sleep_good = sleep_total_minutes is not None and sleep_total_minutes >= 420
    energy_good = energy_score is not None and energy_score >= 80
    high_recent_training = consistency["consistency"] >= 80

    if workout_minutes >= 45 and sleep_good and energy_good:
        return "Productive training day: workout load is meaningful and recovery signals look supportive."

    if high_recent_training and not sleep_good:
        return "Caution: recent workout consistency is high, but sleep is below the preferred recovery threshold."

    if high_recent_training and energy_score is not None and energy_score < 75:
        return "Watch recovery: training consistency is high while Samsung Energy Score is below ideal."

    if workout_minutes == 0 and sleep_good:
        return "Recovery opportunity: sleep looks supportive, and today may be suitable for training if energy feels good."

    return "No major warning from the current simple recovery model."


def build_context():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    snapshot = get_latest_snapshot(cursor)
    if snapshot is None:
        connection.close()
        return "# Vitalis Daily Brief\n\nNo health snapshot found.\n"

    (
        snapshot_date,
        steps,
        distance_meters,
        active_calories,
        average_heart_rate,
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
    ) = snapshot

    latest_date = parse_date(snapshot_date)
    workout_summary = get_workout_summary(cursor, snapshot_date)
    streak = get_streak(cursor, latest_date)
    consistency = get_30_day_consistency(cursor, latest_date)
    recovery_note = get_recovery_note(snapshot, workout_summary, consistency)

    connection.close()

    workout_count, workout_minutes, workout_calories = workout_summary
    distance_km = distance_meters / 1000 if distance_meters is not None else None

    generated_at = datetime.now().isoformat(timespec="seconds")

    return f"""# Vitalis Daily Coach Brief

Generated at: {generated_at}

## Latest Health Date

- Date: {snapshot_date}

## Daily Snapshot

- Steps: {steps if steps is not None else "Unavailable"}
- Distance: {format_number(distance_km, " km", 2)}
- Active calories: {format_number(active_calories, " kcal", 0)}
- Average heart rate: {format_number(average_heart_rate, " bpm")}
- Resting heart rate: {format_number(resting_heart_rate, " bpm")}
- Sleep duration: {format_minutes(sleep_total_minutes)}
- Deep sleep: {format_minutes(deep_sleep_minutes)}
- REM sleep: {format_minutes(rem_sleep_minutes)}
- Light sleep: {format_minutes(light_sleep_minutes)}
- Awake time: {format_minutes(awake_minutes)}
- Samsung Sleep Score: {format_number(sleep_score)}
- Samsung Energy Score: {format_number(energy_score)}
- Energy sleep score: {format_number(energy_sleep_score)}
- Energy activity score: {format_number(energy_activity_score)}

## Today's Workout

- Workout sessions: {workout_count}
- Workout duration: {format_minutes(workout_minutes)}
- Workout calories: {format_number(workout_calories, " kcal", 0)}

## Workout Momentum

- Current workout streak: {streak} days
- Last 30 days workout days: {consistency["workout_days"]}
- Last 30 days workouts: {consistency["workouts"]}
- Last 30 days consistency: {consistency["consistency"]}%
- Last 30 days workout duration: {format_minutes(consistency["workout_minutes"])}

## Vitalis Coach Note

{recovery_note}

## Notes for Vitalis GPT

- Use this file first when the user asks: "How am I doing?"
- Keep the answer concise, evidence-based, and coach-like.
- Mention strengths first, then one caution or focus area if relevant.
- Do not present this as medical advice.
"""


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_context(), encoding="utf-8")
    print(f"Exported Vitalis daily brief to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()