import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path("C:/Projects/Vitalis")

STEPS = [
    PROJECT_DIR / "importers" / "snapshot_importer.py",
    PROJECT_DIR / "exports" / "export_health_context.py",
    PROJECT_DIR / "cloud" / "upload_latest_snapshot.py",
    PROJECT_DIR / "cloud" / "export_supabase_context.py",
]


def run_step(script_path):
    print(f"Running: {script_path}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_DIR,
        check=False,
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
    print(PROJECT_DIR / "exports" / "vitalis_context.md")
    print("Cloud ChatGPT context file:")
    print(PROJECT_DIR / "exports" / "vitalis_cloud_context.md")
    print("Latest snapshot uploaded to Supabase.")


if __name__ == "__main__":
    main()