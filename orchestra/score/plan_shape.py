from __future__ import annotations

from collections import Counter
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
_SMALL = ("XS", "S")


class ShapeWarning(NamedTuple):
    code: str
    subject: str
    message: str


def _depends_on(item: Record) -> list[str]:
    value = item["payload"].get("depends_on")
    if not isinstance(value, list):
        return []
    return [dep for dep in value if isinstance(dep, str)]


def _waves(items: Sequence[Record]) -> dict[str, int]:
    deps = {item["subject"]: _depends_on(item) for item in items}
    waves: dict[str, int] = {}

    def wave(subject: str, path: frozenset[str]) -> int:
        if subject in waves:
            return waves[subject]
        if subject in path:
            return 0
        inner = path | {subject}
        depth = 1 + max((wave(dep, inner) for dep in deps[subject] if dep in deps), default=0)
        if not path:
            waves[subject] = depth
        return depth

    for subject in deps:
        wave(subject, frozenset())
    return waves


def _closes_phase(item: Record, items: Sequence[Record]) -> bool:
    others = {other["subject"] for other in items if other["id"] != item["id"]}
    return bool(others) and others <= set(_depends_on(item))


def plan_shape_warnings(items: Sequence[Record]) -> list[ShapeWarning]:
    waves = _waves(items)
    width = Counter(waves.values())
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
        executor = payload.get("executor") or "subagent"
        if (
            executor == "subagent"
            and size in _SMALL
            and width[waves[subject]] == 1
            and not _closes_phase(item, items)
        ):
            warnings.append(
                ShapeWarning(
                    "small-subagent-solo-wave",
                    subject,
                    f"size {size} subagent task is alone in wave {waves[subject]}; use inline",
                )
            )
    return warnings
