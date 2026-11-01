from collections.abc import Mapping, Sequence

from orchestra.canon.types import JsonValue

Rollup = dict[str, int | float]


def _mapping(value: JsonValue) -> Mapping[str, JsonValue]:
    return value if isinstance(value, dict) else {}


def _number(value: JsonValue) -> int | float:
    return value if isinstance(value, (int, float)) else 0


def _strings(value: JsonValue) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str):
            result.append(item)
    return result


def effort_rollup(rows: Sequence[Mapping[str, JsonValue]]) -> dict[str, Rollup]:
    out: dict[str, Rollup] = {}
    for row in rows:
        records_value = row.get("records")
        if "error" in row or not records_value:
            continue
        records = _mapping(records_value)
        efforts = _strings(records.get("efforts"))
        totals = _mapping(_mapping(row.get("tools")).get("totals"))
        cost = _number(row.get("cost_usd"))
        exclusive = len(efforts) == 1
        for name in efforts:
            e = out.setdefault(
                name,
                {
                    "sessions": 0,
                    "exclusive_sessions": 0,
                    "turns": 0,
                    "tool_calls": 0,
                    "errors": 0,
                    "retries": 0,
                    "cost_shared": 0.0,
                    "cost_exclusive": 0.0,
                },
            )
            e["sessions"] += 1
            e["turns"] += _number(row.get("turns"))
            e["tool_calls"] += _number(totals.get("calls"))
            e["errors"] += _number(totals.get("errors"))
            e["retries"] += _number(totals.get("retries"))
            e["cost_shared"] += cost
            if exclusive:
                e["exclusive_sessions"] += 1
                e["cost_exclusive"] += cost
    return {name: out[name] for name in sorted(out)}
