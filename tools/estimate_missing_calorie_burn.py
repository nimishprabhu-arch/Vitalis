import sqlite3
from pathlib import Path

DB_PATH = Path(r"C:\Projects\Vitalis\database\vitalis.db")

ESTIMATED_REST_CALORIES = 1643.0
ESTIMATION_SOURCE = "health_connect_cloud_sync_estimated_calories"


def main():
    connection = sqlite3.connect(DB_PATH)

    rows = connection.execute(
        """
        select snapshot_date, active_calories
        from daily_health_snapshots
        where active_calories is not null
          and total_burned_calories is null
        order by snapshot_date
        """
    ).fetchall()

    updated = 0

    for snapshot_date, active_calories in rows:
        total_burned = ESTIMATED_REST_CALORIES + float(active_calories)

        connection.execute(
            """
            update daily_health_snapshots
            set
              rest_calories = ?,
              total_burned_calories = ?,
              source = ?
            where snapshot_date = ?
            """,
            (
                ESTIMATED_REST_CALORIES,
                round(total_burned, 2),
                ESTIMATION_SOURCE,
                snapshot_date,
            ),
        )
        updated += 1

    connection.commit()
    connection.close()

    print("Estimated calorie burn complete.")
    print(f"Rows updated: {updated}")
    print(f"Estimated rest calories: {ESTIMATED_REST_CALORIES}")


if __name__ == "__main__":
    main()