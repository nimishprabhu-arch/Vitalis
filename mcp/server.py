from pathlib import Path
import sqlite3
from typing import Any

from fastmcp import FastMCP


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "database" / "vitalis.db"
EXPORTS_DIR = PROJECT_ROOT / "exports"

mcp = FastMCP("Vitalis")


def connect_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def read_text_file(file_name: str) -> str:
    file_path = EXPORTS_DIR / file_name
    if not file_path.exists():
        return f"File not found: {file_path}"
    return file_path.read_text(encoding="utf-8")


@mcp.tool()
def get_latest_snapshot() -> dict[str, Any]:
    """Get the latest daily health snapshot from the Vitalis database."""
    with connect_db() as connection:
        row = connection.execute(
            """
            select *
            from daily_health_snapshots
            order by snapshot_date desc
            limit 1
            """
        ).fetchone()

    return {
        "status": "ok" if row else "empty",
        "snapshot": row_to_dict(row),
    }


@mcp.tool()
def get_health_date_range() -> dict[str, Any]:
    """Get earliest date, latest date, and total daily snapshot count."""
    with connect_db() as connection:
        row = connection.execute(
            """
            select
                min(snapshot_date) as first_date,
                max(snapshot_date) as latest_date,
                count(*) as total_daily_snapshots
            from daily_health_snapshots
            """
        ).fetchone()

    return {
        "status": "ok",
        "date_range": row_to_dict(row),
    }


@mcp.tool()
def get_metric_availability() -> dict[str, Any]:
    """Get availability counts for key Vitalis health metrics."""
    metric_columns = {
        "steps": "steps",
        "distance": "distance_meters",
        "active_calories": "active_calories",
        "floors": "floors",
        "average_heart_rate": "average_heart_rate",
        "minimum_heart_rate": "minimum_heart_rate",
        "maximum_heart_rate": "maximum_heart_rate",
        "resting_heart_rate": "resting_heart_rate",
        "sleep_total_minutes": "sleep_total_minutes",
        "deep_sleep_minutes": "deep_sleep_minutes",
        "rem_sleep_minutes": "rem_sleep_minutes",
        "light_sleep_minutes": "light_sleep_minutes",
        "awake_minutes": "awake_minutes",
        "sleep_score": "sleep_score",
        "sleep_efficiency": "sleep_efficiency",
        "energy_score": "energy_score",
        "energy_sleep_score": "energy_sleep_score",
        "energy_activity_score": "energy_activity_score",
        "heart_health_score": "heart_health_score",
        "workout_session_count": "workout_session_count",
        "workout_total_duration_minutes": "workout_total_duration_minutes",
    }

    with connect_db() as connection:
        total_snapshots = connection.execute(
            "select count(*) from daily_health_snapshots"
        ).fetchone()[0]

        availability = {}

        for label, column_name in metric_columns.items():
            count = connection.execute(
                f"""
                select count(*)
                from daily_health_snapshots
                where {column_name} is not null
                """
            ).fetchone()[0]

            availability[label] = {
                "days_available": count,
                "total_snapshots": total_snapshots,
            }

    return {
        "status": "ok",
        "metric_availability": availability,
    }


@mcp.tool()
def get_workout_summary() -> dict[str, Any]:
    """Get workout coverage, top workout types, and recent workouts."""
    with connect_db() as connection:
        coverage = connection.execute(
            """
            select
                count(*) as total_workouts,
                count(distinct workout_date) as workout_days,
                sum(duration_minutes) as total_duration_minutes,
                sum(calories) as total_calories
            from workouts
            """
        ).fetchone()

        top_types = connection.execute(
            """
            select
                exercise_type_label,
                count(*) as workout_count,
                sum(duration_minutes) as total_duration_minutes,
                avg(duration_minutes) as average_duration_minutes,
                sum(calories) as total_calories
            from workouts
            group by exercise_type_label
            order by workout_count desc
            limit 10
            """
        ).fetchall()

        recent = connection.execute(
            """
            select
                workout_date,
                exercise_type_label,
                duration_minutes,
                calories,
                distance_meters
            from workouts
            order by workout_date desc, start_time desc
            limit 20
            """
        ).fetchall()

    return {
        "status": "ok",
        "coverage": row_to_dict(coverage),
        "top_workout_types": [row_to_dict(row) for row in top_types],
        "recent_workouts": [row_to_dict(row) for row in recent],
    }


@mcp.tool()
def get_daily_brief() -> str:
    """Get the latest Vitalis daily coach brief."""
    return read_text_file("vitalis_daily_brief.md")


@mcp.tool()
def get_health_history_context() -> str:
    """Get the Vitalis historical health context summary."""
    return read_text_file("vitalis_history_context.md")


@mcp.tool()
def get_workout_trends() -> str:
    """Get Vitalis workout trend context."""
    return read_text_file("vitalis_workout_trends_context.md")


@mcp.tool()
def get_training_recovery() -> str:
    """Get Vitalis training load versus recovery context."""
    return read_text_file("vitalis_training_recovery_context.md")


@mcp.tool()
def get_all_context_file_names() -> dict[str, Any]:
    """List available Vitalis exported context files."""
    if not EXPORTS_DIR.exists():
        return {
            "status": "missing",
            "exports_dir": str(EXPORTS_DIR),
            "files": [],
        }

    files = sorted(path.name for path in EXPORTS_DIR.glob("*.md"))

    return {
        "status": "ok",
        "exports_dir": str(EXPORTS_DIR),
        "files": files,
    }


if __name__ == "__main__":
    mcp.run()