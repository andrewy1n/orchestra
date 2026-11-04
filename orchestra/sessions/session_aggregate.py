from __future__ import annotations

import json
import sys
from collections.abc import Iterable

from orchestra.score.effort_rollup import effort_rollup
from orchestra.sessions.session_outliers import outliers
from orchestra.sessions.session_types import (
    JsonObject,
    JsonValue,
    SessionAggregate,
    SessionCaveats,
)
from orchestra.sessions.tool_skill_rollup import tool_skill_rollup

NOTE = (
    "Per-session record counts are approximate: a session counts toward an effort "
    "when a record of that effort falls inside its window, so cost can double-count across efforts."
)


COST_NOTE = (
    "Cost is a lower bound: sessions without a cost-state line in the transcript have no cost data."
)


def _count(value: JsonValue) -> int:
    return value if isinstance(value, int) else 0


def read_rows(lines: Iterable[str]) -> tuple[list[JsonObject], int]:
    rows: list[JsonObject] = []
    bad = 0
    for line in lines:
        if not line.strip():
            continue
        try:
            obj: JsonValue = json.loads(line)
        except ValueError:
            bad += 1
            continue
        if isinstance(obj, dict):
            rows.append(obj)
        else:
            bad += 1
    return rows, bad


def caveats(rows: list[JsonObject], bad: int) -> SessionCaveats:
    attached = ambiguous = with_cost = 0
    for row in rows:
        if "error" not in row and row.get("cost_usd") is not None:
            with_cost += 1
        rec = row.get("records")
        if isinstance(rec, dict):
            attached += _count(rec.get("total"))
            ambiguous += _count(rec.get("ambiguous"))
    return {
        "attached_records": attached,
        "ambiguous_records": ambiguous,
        "ambiguous_share": round(ambiguous / attached, 4) if attached else 0.0,
        "note": NOTE,
        "sessions_with_cost": with_cost,
        "sessions_without_cost": sum("error" not in row for row in rows) - with_cost,
        "cost_note": COST_NOTE,
        "bad_input_lines": bad,
    }


def aggregate(lines: Iterable[str]) -> SessionAggregate:
    rows, bad = read_rows(lines)
    rollup = tool_skill_rollup(rows)
    return {
        "sessions": len(rows),
        "efforts": effort_rollup(rows),
        "tools": rollup["tools"],
        "skills": rollup["skills"],
        "outliers": outliers(rows),
        "caveats": caveats(rows, bad),
    }


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        with open(argv[1]) as file:
            doc = aggregate(file)
    else:
        doc = aggregate(sys.stdin)
    print(json.dumps(doc, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
