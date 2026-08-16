import json
import urllib.request
from datetime import date, datetime, timezone

SUPABASE_URL = "https://ltnlhxsdmcsjpcpxvvxl.supabase.co"
SUPABASE_KEY = "sb_publishable_U55ZW10vDw7fX-kVmWVl0w_8nXnsrOW"
TABLE_NAME = "food_intake"


def ask_float(label, default=None):
    suffix = f" [{default}]" if default is not None else ""
    raw = input(f"{label}{suffix}: ").strip()
    if not raw and default is not None:
        return default
    if not raw:
        return None
    return float(raw)


def ask_text(label, default=""):
    suffix = f" [{default}]" if default else ""
    raw = input(f"{label}{suffix}: ").strip()
    return raw if raw else default


def upload(row):
    body = json.dumps([row]).encode("utf-8")
    request = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}",
        data=body,
        method="POST",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
    )

    with urllib.request.urlopen(request) as response:
        return response.status, response.read().decode("utf-8")


def main():
    intake_date = date.today().isoformat()
    print(f"Date: {intake_date}")

    meal_type = ask_text("Meal type", "breakfast")
    description = ask_text("Food description")

    print("\nPaste GPT estimates. Press Enter to skip unknown values.")
    estimated_calories = ask_float("Calories")
    protein_g = ask_float("Protein g")
    carbs_g = ask_float("Carbs g")
    fat_g = ask_float("Fat g")
    fiber_g = ask_float("Fiber g")
    assumptions = ask_text("Assumptions")
    confidence = ask_text("Confidence", "medium")

    now = datetime.now(timezone.utc).isoformat()

    row = {
        "intake_date": intake_date,
        "meal_type": meal_type,
        "description": description,
        "estimated_calories": estimated_calories,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "fiber_g": fiber_g,
        "assumptions": assumptions,
        "confidence": confidence,
        "source": "gpt_estimate",
        "created_at": now,
        "updated_at": now,
    }

    status, body = upload(row)
    print(f"\nSupabase upload status: {status}")
    print(body)


if __name__ == "__main__":
    main()