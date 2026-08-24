import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEALTH_CONNECT_DB_PATH = ROOT / "tmp" / "health_connect" / "health_connect_export.db"

STEPS = [
    ["cloud/download_health_connect_zip.py"],
    ["cloud/check_health_connect_export_freshness.py"],
    ["cloud/sync_health_connect_to_supabase.py"],
]


def run_step(script_parts):
    script_path = ROOT / script_parts[0]
    env = os.environ.copy()
    env["HEALTH_CONNECT_DB_PATH"] = str(HEALTH_CONNECT_DB_PATH)

    print(f"\n=== Running {script_path.relative_to(ROOT)} ===")
    subprocess.run([sys.executable, str(script_path)], cwd=ROOT, env=env, check=True)


def main():
    for step in STEPS:
        run_step(step)

    print("\nVitalis Health Connect sync complete.")


if __name__ == "__main__":
    main()