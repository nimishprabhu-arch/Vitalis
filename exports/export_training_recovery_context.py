import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "database" / "vitalis.db"
OUTPUT_PATH = PROJECT_ROOT / "exports" / "vitalis_training_recovery_context.md"


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
    consistency = (summary["workout_days"] or 0) / summary["days"]
    avg_minutes_per_day = (summary["workout_minutes"] or 0) / summary["days"]

    if consistency >= 0.85 and avg_minutes_per_day >= 45:
        return "High"
    if consistency >= 0.60 and avg_minutes_per_day >= 25:
        return "Moderate"
    return "Light"


def recovery_label(summary):
    positive = 0
    negative = 0

    sleep_minutes = summary["avg_sleep_minutes"]
    sleep_score = summary["avg_sleep_score"]
    energy_score = summary["avg_energy_score"]

    if sleep_minutes is not None:
        if sleep_minutes >= 420:
            positive += 1
        elif sleep_minutes < 360:
            negative += 1

    if sleep_score is not None:
        if sleep_score >= 80:
            positive += 1
        elif sleep_score < 70:
            negative += 1

    if energy_score is not None:
        if energy_score >= 80:
            positive += 1
        elif energy_score < 70:
            negative += 1

    if negative >= 2:
        return "Strained"
    if positive >= 2:
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


def build_table(summaries):
    lines = [
        "| Period | Workouts | Workout days | Workout duration | Avg sleep | Sleep score | Energy score | Avg HR | Resting HR | Load | Recovery | Vitalis note |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]

    for summary in summaries:
        load = training_load_label(summary)
        recovery = recovery_label(summary)

        lines.append(
            f"| Last {summary['days']} days | "
            f"{summary['workouts']} | "
            f"{summary['workout_days']} | "
            f"{format_minutes(summary['workout_minutes'])} | "
            f"{format_minutes(summary['avg_sleep_minutes'])} | "
            f"{format_value(summary['avg_sleep_score'])} | "
            f"{format_value(summary['avg_energy_score'])} | "
            f"{format_value(summary['avg_heart_rate'], ' bpm')} | "
            f"{format_value(summary['avg_resting_heart_rate'], ' bpm')} | "
            f"{load} | "
            f"{recovery} | "
            f"{risk_note(load, recovery)} |"
        )

    return "\n".join(lines)


def build_context():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    latest_date_text = cursor.execute(
        "select max(snapshot_date) from daily_health_snapshots"
    ).fetchone()[0]

    if latest_date_text is None:
        connection.close()
        return "# Vitalis Training Recovery Context\n\nNo health snapshots found.\n"

    latest_date = parse_date(latest_date_text)
    summaries = [
        fetch_period_summary(cursor, latest_date, 7),
        fetch_period_summary(cursor, latest_date, 14),
        fetch_period_summary(cursor, latest_date, 30),
    ]

    connection.close()

    generated_at = datetime.now().isoformat(timespec="seconds")

    return f"""# Vitalis Training Load vs Recovery Context

Generated at: {generated_at}

## Training Recovery Summary

- Latest health date: {latest_date}
- This file compares recent workout load with recovery signals from sleep, Samsung Sleep Score, Samsung Energy Score, average heart rate, and resting heart rate.

## Training Load vs Recovery

{build_table(summaries)}

## Notes for Vitalis GPT

- Use this file to answer questions about training load, recovery, overtraining risk, and whether today's load looks productive.
- Treat this as an early heuristic model, not a medical diagnosis.
- If load is high and recovery is good, describe it as productive training load.
- If load is high and recovery is mixed or strained, recommend caution, hydration, sleep priority, and avoiding unnecessary extra intensity.
- Compare this file with workout trends and sleep history before making stronger recommendations.
"""


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_context(), encoding="utf-8")
    print(f"Exported Vitalis training recovery context to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()