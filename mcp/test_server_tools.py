from server import (
    get_all_context_file_names,
    get_daily_brief,
    get_health_date_range,
    get_latest_snapshot,
    get_metric_availability,
    get_training_recovery,
    get_workout_summary,
    get_workout_trends,
)


def print_section(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def main() -> None:
    print_section("Vitalis MCP Tool Smoke Test")

    print_section("Health Date Range")
    print(get_health_date_range())

    print_section("Latest Snapshot")
    latest_snapshot = get_latest_snapshot()
    print(latest_snapshot)

    print_section("Metric Availability")
    availability = get_metric_availability()
    print(availability)

    print_section("Workout Summary")
    workout_summary = get_workout_summary()
    print(workout_summary)

    print_section("Context Files")
    print(get_all_context_file_names())

    print_section("Daily Brief Preview")
    print(get_daily_brief()[:1000])

    print_section("Workout Trends Preview")
    print(get_workout_trends()[:1000])

    print_section("Training Recovery Preview")
    print(get_training_recovery()[:1000])

    print()
    print("MCP tool smoke test complete.")


if __name__ == "__main__":
    main()