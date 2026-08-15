import os
import re
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "tmp" / "health_connect"
ZIP_PATH = OUTPUT_DIR / "Health Connect.zip"
DB_PATH = OUTPUT_DIR / "health_connect_export.db"


def extract_drive_file_id(url: str) -> str:
    patterns = [
        r"/file/d/([^/]+)",
        r"[?&]id=([^&]+)",
        r"/open\?id=([^&]+)",
        r"/uc\?id=([^&]+)",
        r"/d/([^/]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    if re.fullmatch(r"[A-Za-z0-9_-]{20,}", url.strip()):
        return url.strip()

    raise ValueError(
        "Could not extract Google Drive file id. Use either the full Drive share link or just the file id."
    )


def download_file(url: str):
    file_id = extract_drive_file_id(url)
    download_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Downloading Health Connect zip from Google Drive...")
    request = urllib.request.Request(
        download_url,
        headers={"User-Agent": "Mozilla/5.0"},
    )

    with urllib.request.urlopen(request) as response:
        ZIP_PATH.write_bytes(response.read())

    print(f"Downloaded zip: {ZIP_PATH}")


def extract_db():
    print("Extracting health_connect_export.db...")

    with zipfile.ZipFile(ZIP_PATH, "r") as archive:
        matches = [
            name for name in archive.namelist()
            if name.endswith("health_connect_export.db")
        ]

        if not matches:
            raise FileNotFoundError("health_connect_export.db not found inside Health Connect.zip")

        with archive.open(matches[0]) as source, DB_PATH.open("wb") as target:
            target.write(source.read())

    print(f"Extracted DB: {DB_PATH}")


def main():
    drive_url = os.environ.get("GOOGLE_DRIVE_ZIP_URL")

    if not drive_url:
        raise RuntimeError("GOOGLE_DRIVE_ZIP_URL secret/env var is missing.")

    download_file(drive_url)
    extract_db()

    print(f"HEALTH_CONNECT_DB_PATH={DB_PATH}")


if __name__ == "__main__":
    main()