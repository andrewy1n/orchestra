from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from orchestra.sessions.types import JsonValue, SessionOutlier


def _mapping(value: JsonValue) -> Mapping[str, JsonValue]:
    return value if isinstance(value, dict) else {}


def _number(value: JsonValue) -> int | float:
    return value if isinstance(value, (int, float)) else 0


def _errors(row: Mapping[str, JsonValue]) -> int | float:
    tools = _mapping(row.get("tools"))
    totals = _mapping(tools.get("totals"))
    return _number(totals.get("errors")) or 0


def _retries(row: Mapping[str, JsonValue]) -> int | float:
    tools = _mapping(row.get("tools"))
    totals = _mapping(tools.get("totals"))
    return _number(totals.get("retries")) or 0


def _cost(row: Mapping[str, JsonValue]) -> float:
    return round(_number(row.get("cost_usd")) or 0, 4)


_METRICS: dict[str, Callable[[Mapping[str, JsonValue]], int | float]] = {
    "errors": _errors,
    "retries": _retries,
    "cost": _cost,
}


def _entry(row: Mapping[str, JsonValue], value: int | float) -> SessionOutlier:
    records = _mapping(row.get("records"))
    effort_value = records.get("efforts")
    efforts = effort_value if isinstance(effort_value, list) else []
    return {
        "session_id": row.get("session_id"),
        "file": row.get("file"),
        "project": row.get("project"),
        "branch": row.get("branch"),
        "efforts": efforts,
        "value": value,
    }


def outliers(
    rows: Sequence[Mapping[str, JsonValue]], top: int = 5
) -> dict[str, list[SessionOutlier]]:
    usable = [row for row in rows if "error" not in row]
    result: dict[str, list[SessionOutlier]] = {}
    for name, getter in _METRICS.items():
        scored = [(getter(row), row) for row in usable]
        scored = [(value, row) for value, row in scored if value]
        scored.sort(key=lambda pair: (-pair[0], str(pair[1].get("session_id"))))
        result[name] = [_entry(row, value) for value, row in scored[:top]]
    return result
