import json
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_DIR = Path("C:/Projects/Vitalis")
OUTPUT_PATH = PROJECT_DIR / "exports" / "vitalis_cloud_context.md"

SUPABASE_URL = "https://ltnlhxsdmcsjpcpxvvxl.supabase.co"
SUPABASE_KEY = "sb_publishable_U55ZW10vDw7fX-kVmWVl0w_8nXnsrOW"


def read_latest_snapshot():
    endpoint = (
        f"{SUPABASE_URL}/rest/v1/health_snapshots"
        "?select=*"
        "&order=snapshot_date.desc"
        "&limit=1"
    )

    request = urllib.request.Request(
        endpoint,
        method="GET",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8")
        raise RuntimeError(f"Supabase error {error.code}: {body}") from error


def minutes_to_hours(minutes):
    if minutes is None:
        return "Unavailable"

    hours = int(minutes) // 60
    remaining_minutes = int(minutes) % 60

    return f"{hours}h {remaining_minutes}m"


def value_or_unavailable(value, suffix=""):
    if value is None:
        return "Unavailable"

    return f"{value}{suffix}"


def build_context(snapshot):
    return f"""# Vitalis Cloud Health Context

This file is generated from the latest Vitalis snapshot stored in Supabase.

## Latest Snapshot

Date: {snapshot.get("snapshot_date")}
Saved at: {snapshot.get("saved_at")}
Source: {snapshot.get("source")}

## Activity

Steps: {value_or_unavailable(snapshot.get("steps"))}
Distance: {value_or_unavailable(snapshot.get("distance_meters"), " meters")}
Active calories: {value_or_unavailable(snapshot.get("active_calories"), " kcal")}
Floors: {value_or_unavailable(snapshot.get("floors"))}

## Heart Rate

Average heart rate: {value_or_unavailable(snapshot.get("average_heart_rate"), " bpm")}
Minimum heart rate: {value_or_unavailable(snapshot.get("minimum_heart_rate"), " bpm")}
Maximum heart rate: {value_or_unavailable(snapshot.get("maximum_heart_rate"), " bpm")}
Resting heart rate: {value_or_unavailable(snapshot.get("resting_heart_rate"), " bpm")}

## Sleep

Total sleep: {minutes_to_hours(snapshot.get("sleep_total_minutes"))}
Deep sleep: {minutes_to_hours(snapshot.get("deep_sleep_minutes"))}
REM sleep: {minutes_to_hours(snapshot.get("rem_sleep_minutes"))}
Light sleep: {minutes_to_hours(snapshot.get("light_sleep_minutes"))}
Awake: {minutes_to_hours(snapshot.get("awake_minutes"))}
Sleep sessions: {value_or_unavailable(snapshot.get("sleep_session_count"))}

## Workouts

Workout sessions: {value_or_unavailable(snapshot.get("workout_session_count"))}
Workout duration: {minutes_to_hours(snapshot.get("workout_total_duration_minutes"))}

## Instructions for ChatGPT

Use this health context to answer questions about Nimish's latest health status.
Do not treat this as medical advice.
Explain uncertainty when data is unavailable or estimated.
"""
    

def main():
    if "PASTE_YOUR" in SUPABASE_KEY:
        raise RuntimeError("Paste your Supabase key before running this script.")

    rows = read_latest_snapshot()

    if not rows:
        raise RuntimeError("No Supabase snapshots found.")

    context = build_context(rows[0])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(context, encoding="utf-8")

    print(f"Exported Vitalis cloud context to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()