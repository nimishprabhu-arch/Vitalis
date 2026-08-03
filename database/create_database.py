import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "vitalis.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def main():
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.executescript(schema)

    print(f"Vitalis database created at: {DATABASE_PATH}")


if __name__ == "__main__":
    main()