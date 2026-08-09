import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


STEPS = [
    PROJECT_ROOT / "importers" / "extract_medical_pdf_text.py",
    PROJECT_ROOT / "importers" / "parse_medical_report_text.py",
    PROJECT_ROOT / "importers" / "medical_lab_importer.py",
    PROJECT_ROOT / "analysis" / "medical_lab_qa.py",

    PROJECT_ROOT / "importers" / "snapshot_importer.py",

    PROJECT_ROOT / "exports" / "export_health_context.py",
    PROJECT_ROOT / "exports" / "export_history_context.py",
    PROJECT_ROOT / "exports" / "export_workout_context.py",
    PROJECT_ROOT / "exports" / "export_workout_trends_context.py",
    PROJECT_ROOT / "exports" / "export_training_recovery_context.py",
    PROJECT_ROOT / "exports" / "export_daily_brief.py",
    PROJECT_ROOT / "exports" / "export_medical_context.py",

    PROJECT_ROOT / "cloud" / "upload_latest_snapshot.py",
    PROJECT_ROOT / "cloud" / "upload_medical_labs.py",
    PROJECT_ROOT / "cloud" / "export_supabase_context.py",
]


def run_step(script_path):
    print(f"Running: {script_path}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Step failed: {script_path}")


def main():
    print("Vitalis daily import started.")
    print("--------------------------------")

    for step in STEPS:
        run_step(step)

    print("--------------------------------")
    print("Vitalis daily import complete.")
    print("Local ChatGPT context file:")
    print(PROJECT_ROOT / "exports" / "vitalis_context.md")
    print("Historical ChatGPT context file:")
    print(PROJECT_ROOT / "exports" / "vitalis_history_context.md")
    print("Workout ChatGPT context file:")
    print(PROJECT_ROOT / "exports" / "vitalis_workout_context.md")
    print("Workout Trends ChatGPT context file:")
    print(PROJECT_ROOT / "exports" / "vitalis_workout_trends_context.md")
    print("Medical ChatGPT context file:")
    print(PROJECT_ROOT / "exports" / "vitalis_medical_context.md")
    print("Cloud ChatGPT context file:")
    print(PROJECT_ROOT / "exports" / "vitalis_cloud_context.md")
    print("Latest snapshot and medical labs uploaded to Supabase.")


if __name__ == "__main__":
    main()