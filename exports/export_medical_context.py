import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "database" / "vitalis.db"
OUTPUT_PATH = ROOT / "exports" / "vitalis_medical_context.md"


def format_value(value):
    if value is None:
        return "Unavailable"

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return str(value)


def fetch_lab_rows(connection):
    return connection.execute(
        """
        select
            test_date,
            panel,
            marker,
            value,
            unit,
            reference_low,
            reference_high,
            flag,
            source_file,
            notes
        from medical_lab_results
        order by test_date desc, panel, marker
        """
    ).fetchall()


def build_context(rows):
    lines = [
        "# Vitalis Medical Context",
        "",
        "## Purpose",
        "",
        "- This file summarizes manually entered medical lab results imported into Vitalis.",
        "- Use this for trend summaries, doctor-prep notes, and health context.",
        "- Do not diagnose. Do not replace medical advice.",
        "",
    ]

    if not rows:
        lines.extend(
            [
                "## Lab Result Coverage",
                "",
                "- No lab results imported yet.",
                "",
            ]
        )
        return "\n".join(lines)

    dates = sorted({row[0] for row in rows})
    markers = sorted({row[2] for row in rows})

    lines.extend(
        [
            "## Lab Result Coverage",
            "",
            f"- First lab date: {dates[0]}",
            f"- Latest lab date: {dates[-1]}",
            f"- Total lab result rows: {len(rows)}",
            f"- Unique markers: {len(markers)}",
            "",
            "## Latest Lab Results",
            "",
            "| Date | Panel | Marker | Value | Unit | Reference Range | Flag |",
            "|---|---|---|---:|---|---|---|",
        ]
    )

    latest_by_marker = {}
    for row in rows:
        marker = row[2]
        if marker not in latest_by_marker:
            latest_by_marker[marker] = row

    for row in latest_by_marker.values():
        test_date, panel, marker, value, unit, reference_low, reference_high, flag, _, _ = row

        reference_range = "Unavailable"
        if reference_low is not None or reference_high is not None:
            reference_range = f"{format_value(reference_low)} - {format_value(reference_high)}"

        lines.append(
            f"| {test_date} | {panel or ''} | {marker} | {format_value(value)} | {unit or ''} | {reference_range} | {flag or ''} |"
        )

    lines.extend(
        [
            "",
            "## Lab History By Marker",
            "",
        ]
    )

    rows_by_marker = defaultdict(list)
    for row in rows:
        rows_by_marker[row[2]].append(row)

    for marker in sorted(rows_by_marker):
        lines.extend(
            [
                f"### {marker}",
                "",
                "| Date | Value | Unit | Flag | Notes |",
                "|---|---:|---|---|---|",
            ]
        )

        for row in sorted(rows_by_marker[marker], key=lambda item: item[0], reverse=True):
            test_date, _, _, value, unit, _, _, flag, _, notes = row
            lines.append(
                f"| {test_date} | {format_value(value)} | {unit or ''} | {flag or ''} | {notes or ''} |"
            )

        lines.append("")

    lines.extend(
        [
            "## Safety Notes",
            "",
            "- Lab values should be interpreted with a qualified clinician.",
            "- Reference ranges vary by lab, age, sex, method, and clinical context.",
            "- Vitalis may summarize trends and highlight values outside supplied ranges, but should not diagnose.",
            "",
        ]
    )

    return "\n".join(lines)


def main():
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = fetch_lab_rows(connection)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_context(rows), encoding="utf-8")

    print(f"Exported Vitalis medical context to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()