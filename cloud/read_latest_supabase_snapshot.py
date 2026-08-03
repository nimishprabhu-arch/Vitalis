import json
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_DIR = Path("C:/Projects/Vitalis")
ENV_PATH = PROJECT_DIR / ".env"


def load_env():
    if not ENV_PATH.exists():
        raise RuntimeError(f"Missing .env file: {ENV_PATH}")

    values = {}

    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()

    return values


def read_latest_snapshot(supabase_url, supabase_key):
    endpoint = (
        f"{supabase_url}/rest/v1/health_snapshots"
        "?select=*"
        "&order=snapshot_date.desc"
        "&limit=1"
    )

    request = urllib.request.Request(
        endpoint,
        method="GET",
        headers={
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8")
        raise RuntimeError(f"Supabase error {error.code}: {body}") from error


def main():
    env = load_env()

    supabase_url = env.get("SUPABASE_URL")
    supabase_key = env.get("SUPABASE_KEY")

    if not supabase_url:
        raise RuntimeError("SUPABASE_URL is missing in .env")

    if not supabase_key:
        raise RuntimeError("SUPABASE_KEY is missing in .env")

    rows = read_latest_snapshot(supabase_url, supabase_key)

    if not rows:
        print("No Supabase snapshots found.")
        return

    snapshot = rows[0]

    print("Latest Vitalis cloud snapshot")
    print("--------------------------------")
    print(f"Date: {snapshot.get('snapshot_date')}")
    print(f"Steps: {snapshot.get('steps')}")
    print(f"Distance: {snapshot.get('distance_meters')} meters")
    print(f"Average HR: {snapshot.get('average_heart_rate')}")
    print(f"Resting HR: {snapshot.get('resting_heart_rate')}")
    print(f"Sleep total: {snapshot.get('sleep_total_minutes')} minutes")


if __name__ == "__main__":
    main()