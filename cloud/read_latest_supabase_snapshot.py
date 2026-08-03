import json
import urllib.error
import urllib.request

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


def main():
    if "PASTE_YOUR" in SUPABASE_KEY:
        raise RuntimeError("Paste your Supabase key before running this script.")

    rows = read_latest_snapshot()

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