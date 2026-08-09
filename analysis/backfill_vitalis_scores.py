import sqlite3
from pathlib import Path

DB_PATH = Path("C:/Projects/Vitalis/database/vitalis.db")


def clamp(value, low=0, high=100):
    return max(low, min(high, int(round(value))))


def score_sleep_quality(row):
    total = row["sleep_total_minutes"] or 0
    deep = row["deep_sleep_minutes"] or 0
    rem = row["rem_sleep_minutes"] or 0
    awake = row["awake_minutes"] or 0

    if total <= 0:
        return None

    duration_score = min(total / 480, 1.0) * 40
    deep_score = min(deep / 90, 1.0) * 25
    rem_score = min(rem / 90, 1.0) * 20
    awake_penalty = min(awake / 90, 1.0) * 15

    return clamp(duration_score + deep_score + rem_score + 15 - awake_penalty)


def score_recovery(row):
    sleep_quality = score_sleep_quality(row)
    resting_hr = row["resting_heart_rate"]
    avg_hr = row["average_heart_rate"]

    parts = []

    if sleep_quality is not None:
        parts.append(sleep_quality)

    if resting_hr:
        if resting_hr <= 65:
            parts.append(90)
        elif resting_hr <= 75:
            parts.append(75)
        elif resting_hr <= 85:
            parts.append(60)
        else:
            parts.append(45)

    if avg_hr:
        if avg_hr <= 80:
            parts.append(85)
        elif avg_hr <= 95:
            parts.append(70)
        elif avg_hr <= 110:
            parts.append(55)
        else:
            parts.append(45)

    if not parts:
        return None

    return clamp(sum(parts) / len(parts))


def score_training_load(row):
    workout_minutes = row["workout_total_duration_minutes"] or 0
    steps = row["steps"] or 0
    avg_hr = row["average_heart_rate"]

    workout_score = min(workout_minutes / 75, 1.0) * 45
    step_score = min(steps / 10000, 1.0) * 35

    hr_score = 10
    if avg_hr:
        if avg_hr < 90:
            hr_score = 10
        elif avg_hr < 120:
            hr_score = 15
        else:
            hr_score = 20

    return clamp(workout_score + step_score + hr_score)


def score_readiness(row):
    sleep_quality = score_sleep_quality(row)
    recovery = score_recovery(row)
    training_load = score_training_load(row)

    parts = []

    if sleep_quality is not None:
        parts.append(sleep_quality * 0.4)

    if recovery is not None:
        parts.append(recovery * 0.4)

    parts.append((100 - abs(training_load - 70)) * 0.2)

    if not parts:
        return None

    return clamp(sum(parts))


def coach_note(readiness, sleep_quality, recovery, training_load):
    if readiness is None:
        return "Not enough data to calculate Vitalis readiness."

    if readiness >= 85 and recovery and recovery >= 75:
        return "Strong readiness. Training looks productive today."

    if training_load and training_load >= 85 and recovery and recovery < 65:
        return "High load with weaker recovery. Prioritize sleep, hydration, and avoid extra intensity."

    if sleep_quality and sleep_quality < 60:
        return "Sleep quality looks low. Keep training lighter and focus on recovery."

    if readiness >= 70:
        return "Readiness looks good. Maintain a balanced training day."

    return "Readiness is mixed. Consider a lighter recovery-focused day."


def ensure_columns(cursor):
    columns = [row[1] for row in cursor.execute("pragma table_info(daily_health_snapshots)").fetchall()]

    required = {
        "vitalis_readiness_score": "INTEGER",
        "vitalis_sleep_quality_score": "INTEGER",
        "vitalis_recovery_score": "INTEGER",
        "vitalis_training_load_score": "INTEGER",
        "vitalis_coach_note": "TEXT",
    }

    for column, column_type in required.items():
        if column not in columns:
            cursor.execute(f"alter table daily_health_snapshots add column {column} {column_type}")


def main():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    ensure_columns(cursor)

    rows = cursor.execute("select * from daily_health_snapshots").fetchall()
    updated = 0

    for row in rows:
        sleep_quality = score_sleep_quality(row)
        recovery = score_recovery(row)
        training_load = score_training_load(row)
        readiness = score_readiness(row)
        note = coach_note(readiness, sleep_quality, recovery, training_load)

        cursor.execute(
            """
            update daily_health_snapshots
            set
                vitalis_readiness_score = ?,
                vitalis_sleep_quality_score = ?,
                vitalis_recovery_score = ?,
                vitalis_training_load_score = ?,
                vitalis_coach_note = ?
            where snapshot_date = ?
            """,
            (
                readiness,
                sleep_quality,
                recovery,
                training_load,
                note,
                row["snapshot_date"],
            ),
        )

        updated += 1

    connection.commit()
    connection.close()

    print(f"Vitalis score backfill complete.")
    print(f"Updated rows: {updated}")


if __name__ == "__main__":
    main()