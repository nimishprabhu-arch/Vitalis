import json
import os
import urllib.request
from datetime import date

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "https://ltnlhxsdmcsjpcpxvvxl.supabase.co",
)
SUPABASE_URL = "https://ltnlhxsdmcsjpcpxvvxl.supabase.co"
SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    "sb_publishable_U55ZW10vDw7fX-kVmWVl0w_8nXnsrOW",
    )

TABLE_NAME = "body_metrics"


def ask(prompt, default=None):
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value if value else default


def number_or_none(value):
    if value in (None, ""):
        return None
    return float(value)


def integer_or_none(value):
    if value in (None, ""):
        return None
    return int(value)


def upload(row):
    if not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_KEY environment variable is missing.")

    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?on_conflict=metric_date"

    payload = json.dumps([row]).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=representation",
        },
    )

    with urllib.request.urlopen(request) as response:
        return response.status, response.read().decode("utf-8")


def main():
    print("Vitalis Body Metric Entry")
    print("-------------------------")

    metric_date = date.today().isoformat()
    print(f"Date: {metric_date}")
    weight_kg = ask("Weight kg")
    systolic_bp = ask("Systolic BP")
    diastolic_bp = ask("Diastolic BP")
    notes = ask("Notes", "")

    row = {
        "metric_date": metric_date,
        "weight_kg": number_or_none(weight_kg),
        "systolic_bp": integer_or_none(systolic_bp),
        "diastolic_bp": integer_or_none(diastolic_bp),
        "notes": notes,
        "source": "manual_entry",
    }

    status, body = upload(row)

    print("Upload complete.")
    print(f"Status: {status}")
    print(body)


if __name__ == "__main__":
    main()