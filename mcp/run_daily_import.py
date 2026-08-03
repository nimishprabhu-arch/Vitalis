import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path("C:/Projects/Vitalis")

IMPORTER_SCRIPT = PROJECT_DIR / "importers" / "snapshot_importer.py"
EXPORT_SCRIPT = PROJECT_DIR / "exports" / "export_health_context.py"


def run_script(script_path):
    print(f"Running: {script_path}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(script_path.parent),
        text=True,
        capture_output=True,
    )

    if result.stdout:
        print(result.stdout.strip())

    if result.stderr:
        print(result.stderr.strip())

    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {script_path}")


def main():
    print("Vitalis daily import started.")
    print("--------------------------------")

    run_script(IMPORTER_SCRIPT)
    run_script(EXPORT_SCRIPT)

    print("--------------------------------")
    print("Vitalis daily import complete.")
    print("Your ChatGPT context file is ready:")
    print(PROJECT_DIR / "exports" / "vitalis_context.md")


if __name__ == "__main__":
    main()