from __future__ import annotations

from pathlib import Path
from statistics import median
from typing import TypedDict

from orchestra.metrics.instants import parse_instant
from orchestra.metrics.phases import PhaseRow, build_phase_rows

COLUMNS = (
    "tasks",
    "elapsed_seconds",
    "review_rounds",
    "failed_check_runs",
    "human_decisions",
    "operations_per_task",
)
UNRECORDED = "unrecorded"


class Cell(TypedDict):
    median: float | None
    n: int


class WeightGroup(TypedDict):
    phases: int
    columns: dict[str, Cell]


class Side(TypedDict):
    phases: int
    weights: dict[str, WeightGroup]


class Comparison(TypedDict):
    boundary: str
    sides: dict[str, Side]
    unplaced: int


class UnknownBoundaryError(ValueError):
    pass


def _summarize(rows: list[PhaseRow]) -> Side:
    weights: dict[str, WeightGroup] = {}
    for weight in sorted({r.weight or UNRECORDED for r in rows}):
        group = [r for r in rows if (r.weight or UNRECORDED) == weight]
        columns: dict[str, Cell] = {}
        for column in COLUMNS:
            values: list[float] = [v for r in group if (v := getattr(r, column)) is not None]
            columns[column] = {"median": median(values) if values else None, "n": len(values)}
        weights[weight] = {"phases": len(group), "columns": columns}
    return {"phases": len(rows), "weights": weights}


def compare_phases(directory: Path, boundary: str) -> Comparison:
    rows = build_phase_rows(directory)
    anchor = next((r for r in rows if r.phase == boundary), None)
    if anchor is None:
        raise UnknownBoundaryError(f"no done phase named {boundary}")
    if anchor.landing_time is None:
        raise UnknownBoundaryError(f"phase {boundary} has no landing time")
    cut = parse_instant(anchor.landing_time)
    before: list[PhaseRow] = []
    after: list[PhaseRow] = []
    unplaced = 0
    for r in rows:
        if r is anchor:
            continue
        if r.landing_time is None:
            unplaced += 1
        elif parse_instant(r.landing_time) < cut:
            before.append(r)
        else:
            after.append(r)
    return {
        "boundary": boundary,
        "sides": {"before": _summarize(before), "after": _summarize(after)},
        "unplaced": unplaced,
    }


def render_text(comparison: Comparison) -> str:
    lines = [f"boundary\t{comparison['boundary']}"]
    for side, summary in comparison["sides"].items():
        lines.append(f"{side}\t{summary['phases']} phases")
        for weight, group in summary["weights"].items():
            lines.append(f"  {weight}\t{group['phases']} phases")
            for column, cell in group["columns"].items():
                shown = "-" if cell["median"] is None else cell["median"]
                lines.append(f"    {column}\t{shown}\t{cell['n']}")
    lines.append(f"unplaced\t{comparison['unplaced']}")
    return "\n".join(lines)
