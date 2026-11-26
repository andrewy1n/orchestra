from __future__ import annotations

from collections.abc import Sequence
from statistics import median

from orchestra.canon.types import Record

SIZES = ("XS", "S", "M", "L", "XL")
REPORT_LIMIT = 100


def _numeric(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def measured_size_lines(records: Sequence[Record]) -> tuple[str, ...]:
    sizes = {
        record["subject"]: record["payload"].get("size")
        for record in records
        if record["record_type"] == "score:work-item"
    }
    reports = sorted(
        (
            record
            for record in records
            if record["record_type"] == "conductor:execution-report"
            and _numeric(record["payload"].get("duration_s"))
        ),
        key=lambda record: record["recorded_at"],
        reverse=True,
    )[:REPORT_LIMIT]
    minutes: dict[str, list[float]] = {size: [] for size in SIZES}
    for report in reports:
        size = sizes.get(str(report["payload"].get("work_item")))
        if size in minutes:
            minutes[str(size)].append(float(report["payload"]["duration_s"]) / 60)  # pyright: ignore[reportArgumentType]
    lines: list[str] = []
    for size in SIZES:
        values = minutes[size]
        if not values:
            lines.append(f"- {size}: no data")
            continue
        noun = "sample" if len(values) == 1 else "samples"
        lines.append(f"- {size}: {median(values):.1f} min median, {len(values)} {noun}")
    return tuple(lines)
