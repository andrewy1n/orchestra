from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple

from orchestra.canon.types import Record

SIZE_BANDS: dict[str, tuple[int, int]] = {
    "XS": (2, 5),
    "S": (5, 10),
    "M": (8, 15),
    "L": (15, 25),
    "XL": (25, 40),
}
MAX_REQUIREMENTS = 4


class ShapeWarning(NamedTuple):
    code: str
    subject: str
    message: str


def plan_shape_warnings(items: Sequence[Record]) -> list[ShapeWarning]:
    warnings: list[ShapeWarning] = []
    for item in items:
        if item["lifecycle_state"] != "planned":
            continue
        subject = item["subject"]
        payload = item["payload"]
        size = payload.get("size")
        estimate = payload.get("estimate_minutes")
        requirements = payload.get("requirements")
        count = len(requirements) if isinstance(requirements, list) else 0
        if size == "XL":
            warnings.append(
                ShapeWarning("task-split-candidate", subject, "size XL; split the task")
            )
        elif count > MAX_REQUIREMENTS:
            warnings.append(
                ShapeWarning(
                    "task-split-candidate",
                    subject,
                    f"carries {count} requirements, more than {MAX_REQUIREMENTS}; split the task",
                )
            )
        if isinstance(size, str) and size in SIZE_BANDS and type(estimate) is int:
            low, high = SIZE_BANDS[size]
            if not low <= estimate <= high:
                warnings.append(
                    ShapeWarning(
                        "estimate-outside-size-band",
                        subject,
                        f"estimate_minutes {estimate} is outside the {size} band {low}-{high}",
                    )
                )
    return warnings
