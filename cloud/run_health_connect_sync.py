import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS = [
    ["importers/import_health_connect_db_metrics.py"],
    ["importers/import_health_connect_workouts.py"],
    ["cloud/upload_all_snapshots.py"],
    ["cloud/upload_workouts.py"],
]


def run_step(script_parts):
    script_path = ROOT / script_parts[0]
    print(f"\n=== Running {script_path.relative_to(ROOT)} ===")
    subprocess.run([sys.executable, str(script_path)], cwd=ROOT, check=True)


def main():
    for step in STEPS:
        run_step(step)

    print("\nVitalis Health Connect sync complete.")


if __name__ == "__main__":
    main()