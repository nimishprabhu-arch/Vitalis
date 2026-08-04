import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "database" / "vitalis.db"


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


def format_value(value, suffix="", decimals=1):
    if value is None:
        return "Unavailable"

    return f"{round(value, decimals)}{suffix}"


def fetch_period_summary(cursor, latest_date, days):
    start_date = latest_date - timedelta(days=days - 1)

    row = cursor.execute(
        """
        select
            count(w.workout_date) as workouts,
            count(distinct w.workout_date) as workout_days,
            round(coalesce(sum(w.duration_minutes), 0), 2) as workout_minutes,
            round(coalesce(sum(w.calories), 0), 2) as workout_calories,
            round(avg(d.sleep_total_minutes), 2) as avg_sleep_minutes,
            round(avg(d.sleep_score), 2) as avg_sleep_score,
            round(avg(d.energy_score), 2) as avg_energy_score,
            round(avg(d.average_heart_rate), 2) as avg_heart_rate,
            round(avg(d.resting_heart_rate), 2) as avg_resting_heart_rate
        from daily_health_snapshots d
        left join workouts w
            on d.snapshot_date = w.workout_date
        where d.snapshot_date between ? and ?
        """,
        (start_date.isoformat(), latest_date.isoformat()),
    ).fetchone()

    return {
        "days": days,
        "start_date": start_date,
        "end_date": latest_date,
        "workouts": row[0],
        "workout_days": row[1],
        "workout_minutes": row[2],
        "workout_calories": row[3],
        "avg_sleep_minutes": row[4],
        "avg_sleep_score": row[5],
        "avg_energy_score": row[6],
        "avg_heart_rate": row[7],
        "avg_resting_heart_rate": row[8],
    }


def training_load_label(summary):
    days = summary["days"]
    workout_days = summary["workout_days"] or 0
    workout_minutes = summary["workout_minutes"] or 0

    consistency = workout_days / days
    avg_minutes_per_day = workout_minutes / days

    if consistency >= 0.85 and avg_minutes_per_day >= 45:
        return "High"
    if consistency >= 0.60 and avg_minutes_per_day >= 25:
        return "Moderate"
    return "Light"


def recovery_label(summary):
    sleep_minutes = summary["avg_sleep_minutes"]
    sleep_score = summary["avg_sleep_score"]
    energy_score = summary["avg_energy_score"]

    positive_signals = 0
    negative_signals = 0

    if sleep_minutes is not None:
        if sleep_minutes >= 420:
            positive_signals += 1
        elif sleep_minutes < 360:
            negative_signals += 1

    if sleep_score is not None:
        if sleep_score >= 80:
            positive_signals += 1
        elif sleep_score < 70:
            negative_signals += 1

    if energy_score is not None:
        if energy_score >= 80:
            positive_signals += 1
        elif energy_score < 70:
            negative_signals += 1

    if negative_signals >= 2:
        return "Strained"
    if positive_signals >= 2:
        return "Good"
    return "Mixed"


def risk_note(load, recovery):
    if load == "High" and recovery == "Strained":
        return "Elevated risk: high training load with weak recovery signals."
    if load == "High" and recovery == "Mixed":
        return "Watch closely: training load is high and recovery is not clearly strong."
    if load == "High" and recovery == "Good":
        return "Productive load: high training volume with supportive recovery signals."
    if load == "Moderate" and recovery == "Strained":
        return "Recovery may need attention despite moderate training load."
    if load == "Light" and recovery == "Good":
        return "Recovery looks strong relative to current training load."
    return "No major training-recovery warning from this simple model."


def print_summary(summary):
    load = training_load_label(summary)
    recovery = recovery_label(summary)

    print(f"Last {summary['days']} days")
    print("-" * 20)
    print(f"Workout days: {summary['workout_days']}")
    print(f"Workouts: {summary['workouts']}")
    print(f"Workout duration: {format_minutes(summary['workout_minutes'])}")
    print(f"Workout calories: {round(summary['workout_calories'] or 0):,} kcal")
    print(f"Average sleep: {format_minutes(summary['avg_sleep_minutes'])}")
    print(f"Average sleep score: {format_value(summary['avg_sleep_score'])}")
    print(f"Average energy score: {format_value(summary['avg_energy_score'])}")
    print(f"Average heart rate: {format_value(summary['avg_heart_rate'], ' bpm')}")
    print(f"Average resting heart rate: {format_value(summary['avg_resting_heart_rate'], ' bpm')}")
    print(f"Training load: {load}")
    print(f"Recovery signal: {recovery}")
    print(f"Vitalis note: {risk_note(load, recovery)}")
    print()


def main():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    latest_date_text = cursor.execute(
        "select max(snapshot_date) from daily_health_snapshots"
    ).fetchone()[0]

    if latest_date_text is None:
        print("No daily health snapshots found.")
        return

    latest_date = parse_date(latest_date_text)

    print("Vitalis Training Load vs Recovery v1")
    print("------------------------------------")
    print(f"Latest health date: {latest_date}")
    print()

    for days in [7, 14, 30]:
        summary = fetch_period_summary(cursor, latest_date, days)
        print_summary(summary)

    connection.close()


if __name__ == "__main__":
    main()