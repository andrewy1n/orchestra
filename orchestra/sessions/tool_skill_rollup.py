from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypedDict

from orchestra.sessions.session_types import JsonValue, SkillRollup, ToolRollup


class ToolSkillRollup(TypedDict):
    tools: list[ToolRollup]
    skills: list[SkillRollup]


def _mapping(value: JsonValue) -> Mapping[str, JsonValue]:
    return value if isinstance(value, dict) else {}


def _count(value: JsonValue) -> int:
    return value if isinstance(value, int) else 0


def tool_skill_rollup(
    rows: Sequence[Mapping[str, JsonValue]],
) -> ToolSkillRollup:
    tools: dict[str, dict[str, int]] = {}
    skills: dict[str, dict[str, int]] = {}
    for row in rows:
        if "error" in row:
            continue
        tool_container = _mapping(row.get("tools"))
        for name, stats_value in _mapping(tool_container.get("tools")).items():
            stats = _mapping(stats_value)
            calls = _count(stats.get("calls"))
            if calls <= 0:
                continue
            agg = tools.setdefault(name, {"calls": 0, "errors": 0, "retries": 0, "sessions": 0})
            agg["calls"] += calls
            agg["errors"] += _count(stats.get("errors"))
            agg["retries"] += _count(stats.get("retries"))
            agg["sessions"] += 1
        for name, count_value in _mapping(row.get("skills")).items():
            count = _count(count_value)
            if count <= 0:
                continue
            agg = skills.setdefault(name, {"invocations": 0, "sessions": 0})
            agg["invocations"] += count
            agg["sessions"] += 1
    tool_rows: list[ToolRollup] = [
        {
            "name": name,
            "calls": aggregate["calls"],
            "errors": aggregate["errors"],
            "error_rate": round(aggregate["errors"] / aggregate["calls"], 4)
            if aggregate["calls"]
            else 0.0,
            "retries": aggregate["retries"],
            "sessions": aggregate["sessions"],
        }
        for name, aggregate in tools.items()
    ]
    skill_rows: list[SkillRollup] = [
        {
            "name": name,
            "invocations": aggregate["invocations"],
            "sessions": aggregate["sessions"],
        }
        for name, aggregate in skills.items()
    ]
    tool_rows.sort(key=lambda row: (-row["calls"], row["name"]))
    skill_rows.sort(key=lambda row: (-row["invocations"], row["name"]))
    return {"tools": tool_rows, "skills": skill_rows}
