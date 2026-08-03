import sqlite3
from pathlib import Path

PROJECT_DIR = Path("C:/Projects/Vitalis")
DATABASE_PATH = PROJECT_DIR / "database" / "vitalis.db"
OUTPUT_PATH = PROJECT_DIR / "exports" / "vitalis_history_context.md"


def avg(values):
    clean = [value for value in values if value is not None]
    if not clean:
        return None
    return sum(clean) / len(clean)


def fmt_number(value, decimals=0):
    if value is None:
        return "Unavailable"
    return f"{value:.{decimals}f}"


def fmt_minutes(value):
    if value is None:
        return "Unavailable"

    value = int(value)
    hours = value // 60
    minutes = value % 60
    return f"{hours}h {minutes}m"


def fetch_rows():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            """
            SELECT *
            FROM daily_health_snapshots
            ORDER BY snapshot_date ASC
            """
        ).fetchall()


def summarize_period(rows):
    return {
        "days": len(rows),
        "avg_steps": avg([row["steps"] for row in rows]),
        "avg_distance_meters": avg([row["distance_meters"] for row in rows]),
        "avg_active_calories": avg([row["active_calories"] for row in rows]),
        "avg_heart_rate": avg([row["average_heart_rate"] for row in rows]),
        "avg_resting_heart_rate": avg([row["resting_heart_rate"] for row in rows]),
        "avg_sleep_minutes": avg([row["sleep_total_minutes"] for row in rows]),
        "avg_deep_sleep_minutes": avg([row["deep_sleep_minutes"] for row in rows]),
        "avg_rem_sleep_minutes": avg([row["rem_sleep_minutes"] for row in rows]),
        "avg_light_sleep_minutes": avg([row["light_sleep_minutes"] for row in rows]),
    }


def available_count(rows, column):
    return sum(1 for row in rows if row[column] is not None)


def build_context(rows):
    if not rows:
        raise RuntimeError("No health data found.")

    latest = rows[-1]
    last_30 = rows[-30:]
    last_90 = rows[-90:]

    all_time = summarize_period(rows)
    summary_30 = summarize_period(last_30)
    summary_90 = summarize_period(last_90)

    return f"""# Vitalis Historical Health Context

This file summarizes Nimish's historical Vitalis health data.

## Data Coverage

First date: {rows[0]["snapshot_date"]}
Latest date: {latest["snapshot_date"]}
Total daily snapshots: {len(rows)}

## Latest Snapshot

Date: {latest["snapshot_date"]}

Steps: {fmt_number(latest["steps"])}
Distance: {fmt_number(latest["distance_meters"], 1)} meters
Active calories: {fmt_number(latest["active_calories"], 1)} kcal

Average heart rate: {fmt_number(latest["average_heart_rate"], 1)} bpm
Minimum heart rate: {fmt_number(latest["minimum_heart_rate"])} bpm
Maximum heart rate: {fmt_number(latest["maximum_heart_rate"])} bpm
Resting heart rate: {fmt_number(latest["resting_heart_rate"])} bpm

Sleep total: {fmt_minutes(latest["sleep_total_minutes"])}
Deep sleep: {fmt_minutes(latest["deep_sleep_minutes"])}
REM sleep: {fmt_minutes(latest["rem_sleep_minutes"])}
Light sleep: {fmt_minutes(latest["light_sleep_minutes"])}
Awake: {fmt_minutes(latest["awake_minutes"])}

## Last 30 Days

Days available: {summary_30["days"]}

Average steps: {fmt_number(summary_30["avg_steps"])}
Average distance: {fmt_number(summary_30["avg_distance_meters"], 1)} meters
Average active calories: {fmt_number(summary_30["avg_active_calories"], 1)} kcal
Average heart rate: {fmt_number(summary_30["avg_heart_rate"], 1)} bpm
Average resting heart rate: {fmt_number(summary_30["avg_resting_heart_rate"], 1)} bpm
Average sleep: {fmt_minutes(summary_30["avg_sleep_minutes"])}
Average deep sleep: {fmt_minutes(summary_30["avg_deep_sleep_minutes"])}
Average REM sleep: {fmt_minutes(summary_30["avg_rem_sleep_minutes"])}
Average light sleep: {fmt_minutes(summary_30["avg_light_sleep_minutes"])}

## Last 90 Days

Days available: {summary_90["days"]}

Average steps: {fmt_number(summary_90["avg_steps"])}
Average distance: {fmt_number(summary_90["avg_distance_meters"], 1)} meters
Average active calories: {fmt_number(summary_90["avg_active_calories"], 1)} kcal
Average heart rate: {fmt_number(summary_90["avg_heart_rate"], 1)} bpm
Average resting heart rate: {fmt_number(summary_90["avg_resting_heart_rate"], 1)} bpm
Average sleep: {fmt_minutes(summary_90["avg_sleep_minutes"])}
Average deep sleep: {fmt_minutes(summary_90["avg_deep_sleep_minutes"])}
Average REM sleep: {fmt_minutes(summary_90["avg_rem_sleep_minutes"])}
Average light sleep: {fmt_minutes(summary_90["avg_light_sleep_minutes"])}

## All-Time Averages

Average steps: {fmt_number(all_time["avg_steps"])}
Average distance: {fmt_number(all_time["avg_distance_meters"], 1)} meters
Average active calories: {fmt_number(all_time["avg_active_calories"], 1)} kcal
Average heart rate: {fmt_number(all_time["avg_heart_rate"], 1)} bpm
Average resting heart rate: {fmt_number(all_time["avg_resting_heart_rate"], 1)} bpm
Average sleep: {fmt_minutes(all_time["avg_sleep_minutes"])}

## Data Availability

Steps days: {available_count(rows, "steps")}
Distance days: {available_count(rows, "distance_meters")}
Active calorie days: {available_count(rows, "active_calories")}
Heart rate days: {available_count(rows, "average_heart_rate")}
Resting heart rate days: {available_count(rows, "resting_heart_rate")}
Sleep days: {available_count(rows, "sleep_total_minutes")}
Deep sleep days: {available_count(rows, "deep_sleep_minutes")}
REM sleep days: {available_count(rows, "rem_sleep_minutes")}
Light sleep days: {available_count(rows, "light_sleep_minutes")}

## Known Limitations

Samsung Energy Score is not yet imported.
Samsung Sleep Score is not yet imported.
Deep sleep may be incomplete until sleep stage importer v2 is added.
Resting heart rate may be incomplete for historical days.
Some Samsung-specific metrics may need separate Samsung export parsing.

## Instructions for ChatGPT

Use this file for trend-aware health analysis.
Compare latest values against 30-day, 90-day, and all-time averages.
Clearly identify missing or incomplete data.
Do not provide medical diagnosis.
"""


def main():
    rows = fetch_rows()
    context = build_context(rows)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(context, encoding="utf-8")

    print(f"Exported Vitalis history context to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()