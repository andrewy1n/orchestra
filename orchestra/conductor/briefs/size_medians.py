from __future__ import annotations

from collections.abc import Sequence
from statistics import median

from orchestra.canon.types import Record
from orchestra.score.lookups import record_order

SIZES = ("XS", "S", "M", "L", "XL")
REPORT_LIMIT = 100


def _numeric(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def measured_size_lines(records: Sequence[Record]) -> tuple[str, ...]:
    sizes = {
        record["subject"]: record["payload"].get("size")
        for record in sorted(
            (record for record in records if record["record_type"] == "score:work-item"),
            key=record_order,
        )
    }
    reports = sorted(
        (
            record
            for record in records
            if record["record_type"] == "conductor:execution-report"
            and _numeric(record["payload"].get("duration_s"))
        ),
        key=record_order,
        reverse=True,
    )
    minutes: dict[str, list[float]] = {size: [] for size in SIZES}
    seen: set[str] = set()
    for report in reports:
        if len(seen) == REPORT_LIMIT:
            break
        item = str(report["payload"].get("work_item"))
        size = sizes.get(item)
        if size not in minutes or item in seen:
            continue
        seen.add(item)
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
