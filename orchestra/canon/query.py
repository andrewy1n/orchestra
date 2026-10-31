"""Freeform record matching for `list` and future read-path callers.

A `list` query spans record types, matches subjects by prefix, searches body
prose with a regex, and takes its filter values as raw CLI strings.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from re import Pattern
from typing import Any

from orchestra.canon.types import JsonObject, JsonValue, Record

# derived is read-time only (see derive.py) but a --where clause treats it
# like any other namespaced field -- an agent asking "what's ready" shouldn't
# care that the value isn't stored on disk.
WHERE_NAMESPACES = ("payload", "derived")
WHERE_TOP_LEVEL = ("subject", "lifecycle_state")
DEFAULT_EXCERPT_LIMIT = 160


class QueryError(Exception):
    pass


_MISSING = object()


def _coerce_value(raw: str) -> Any:
    """Best-effort JSON-decode a --where value so `true`/`42`/`"x"` compare
    against their typed payload counterparts; anything else is a literal
    string."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _split_where_item(item: str) -> tuple[str, str, str]:
    """Return (field, op, raw_value) for a single --where clause.

    Ops: ``eq`` (``=``), ``ne`` (``!=``). ``any_of:`` is an equals-value prefix
    handled by the caller after split.
    """
    ne_at = item.find("!=")
    eq_at = item.find("=")
    if ne_at >= 0 and (eq_at < 0 or ne_at < eq_at):
        return item[:ne_at], "ne", item[ne_at + 2 :]
    if eq_at < 0:
        raise QueryError(
            f"invalid --where {item!r}; expected payload.<field>=<value> "
            "or payload.<field>!=<value>"
        )
    return item[:eq_at], "eq", item[eq_at + 1 :]


def _parse_where_value(raw: str, op: str) -> tuple[str, Any]:
    """Map raw value + base op into (op, coerced_value).

    ``any_of:a,b,c`` on an equals clause becomes op ``any_of`` with a list.
    """
    if op == "eq" and raw.startswith("any_of:"):
        parts = raw[len("any_of:") :].split(",")
        return "any_of", [_coerce_value(part) for part in parts]
    return op, _coerce_value(raw)


def parse_where(raw: Iterable[str] | None) -> list[tuple[str, str, str, JsonValue]]:
    """Parse repeatable --where flags into (namespace, field, op, value).

    ``field`` may be dotted (``meta.tier``) for nested payload/derived walks.
    ``op`` is ``eq``, ``ne``, or ``any_of``.
    """
    filters: list[tuple[str, str, str, Any]] = []
    for item in raw or []:
        field, base_op, raw_value = _split_where_item(item)
        op, value = _parse_where_value(raw_value, base_op)
        namespace, sep, subfield = field.partition(".")
        if not sep and field in WHERE_TOP_LEVEL:
            filters.append(("record", field, op, value))
            continue
        if not sep or namespace not in WHERE_NAMESPACES:
            raise QueryError(
                f"invalid --where {item!r}; use subject, lifecycle_state, "
                "payload.<field>, or derived.<field>"
            )
        if not subfield:
            raise QueryError(f"invalid --where {item!r}; missing {namespace} field name")
        filters.append((namespace, subfield, op, value))
    return filters


def resolve_path(bucket: object, field_path: str) -> object:
    """Walk dotted ``field_path`` through nested dicts; ``_MISSING`` if absent."""
    cur: Any = bucket
    for part in field_path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return _MISSING
        cur = cur[part]
    return cur


def compile_grep(pattern: str | None) -> Pattern[str] | None:
    """Compile a --grep pattern once; None means "no body filter"."""
    if pattern is None:
        return None
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        raise QueryError(f"invalid --grep pattern {pattern!r}: {exc}") from exc


def _same(actual: Any, expected: Any) -> bool:
    # bool is an int subclass, so plain == makes 1 match True. Keep them distinct.
    if isinstance(actual, bool) != isinstance(expected, bool):
        return False
    return actual == expected


def where_matches(record: Record, filters: list[tuple[str, str, str, JsonValue]]) -> bool:
    for namespace, field, op, value in filters:
        if namespace == "record":
            actual = record.get(field, _MISSING)
        else:
            actual = resolve_path(record.get(namespace) or {}, field)
        if actual is _MISSING:
            # An absent field is not a null field; =null / !=x / any_of must not
            # match "never set".
            return False
        if op == "eq":
            if not _same(actual, value):
                return False
        elif op == "ne":
            if _same(actual, value):
                return False
        elif op == "any_of":
            if not any(_same(actual, candidate) for candidate in value):
                return False
        else:
            raise QueryError(f"unknown where op {op!r}")
    return True


def subject_matches(record: Record, subject: str | None, *, exact: bool = False) -> bool:
    if subject is None:
        return True
    actual = record.get("subject") or ""
    return actual == subject if exact else actual == subject or actual.startswith(subject)


def body_matches(record: Record, grep: Pattern[str] | None) -> bool:
    if grep is None:
        return True
    return grep.search(record.get("body") or "") is not None


def has_inbound(record: Record, rel_type: str) -> bool:
    """True if `derived.referenced_by` (see derive.compute_inverse) has at
    least one source recorded under `rel_type`."""
    by_type = (record.get("derived") or {}).get("referenced_by") or {}
    return bool(by_type.get(rel_type))


def within_time_range(record: Record, since: str | None, until: str | None) -> bool:
    """`recorded_at` string-compares against ISO-8601 bounds (valid because
    `_now()` is fixed-width UTC). A record with no `recorded_at` (written
    before this field existed) fails any bounded query -- conservative,
    since "unknown when" cannot be asserted to fall inside a range."""
    if since is None and until is None:
        return True
    recorded_at = record.get("recorded_at")
    if not recorded_at:
        return False
    if since is not None and recorded_at < since:
        return False
    return not (until is not None and recorded_at > until)


def order_by_recorded_at(records: list[Record], *, reverse: bool = False) -> list[Record]:
    """Stable sort by `recorded_at`; records missing it (pre-existing,
    backward-compat) sort first regardless of `reverse` -- "unknown when" is
    not "most recent", so `reverse` must only flip ordering among records
    that actually have a timestamp, not push the unknowns to the other end."""
    missing = [record for record in records if not record.get("recorded_at")]
    present = [record for record in records if record.get("recorded_at")]
    present.sort(key=lambda record: record["recorded_at"], reverse=reverse)
    return missing + present


def order_by_path(records: list[Record], path: str, *, reverse: bool = False) -> list[Record]:
    """Sort by a top-level or dotted ``payload.*`` / ``derived.*`` path.

    Missing values sort first (stable with recorded_at missing behavior).
    """

    def lookup(record: Record) -> object:
        if path in ("subject", "lifecycle_state", "recorded_at"):
            return record.get(path, _MISSING)
        namespace, sep, sub = path.partition(".")
        if not sep:
            return record.get(path, _MISSING)
        if namespace in WHERE_NAMESPACES:
            return resolve_path(record.get(namespace) or {}, sub)
        return record.get(path, _MISSING)

    missing = [r for r in records if lookup(r) is _MISSING]
    present = [r for r in records if lookup(r) is not _MISSING]
    present.sort(key=lambda r: lookup(r), reverse=reverse)
    return missing + present


def record_matches(
    record: Record,
    *,
    where_filters: list[tuple[str, str, str, JsonValue]] | None = None,
    subject: str | None = None,
    exact_subject: bool = False,
    grep: Pattern[str] | None = None,
    since: str | None = None,
    until: str | None = None,
    has_inbound_types: list[str] | None = None,
) -> bool:
    """AND all active predicates, cheapest first.

    Payload/derived/subject checks are dict lookups and string comparisons;
    the body regex only runs on records that already survived those, so a
    where-only query never pays for a body search, and a query that also
    filters by subject or where never regex-scans bodies it was always going
    to reject.
    """
    if not where_matches(record, where_filters or []):
        return False
    if not subject_matches(record, subject, exact=exact_subject):
        return False
    if not within_time_range(record, since, until):
        return False
    for rel_type in has_inbound_types or []:
        if not has_inbound(record, rel_type):
            return False
    return body_matches(record, grep)


def _first_nonblank_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def matching_line(record: Record, grep: Pattern[str]) -> str | None:
    for line in (record.get("body") or "").splitlines():
        if grep.search(line):
            return line.strip()
    return None


def truncate(text: str, limit: int = DEFAULT_EXCERPT_LIMIT) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: max(limit - 1, 0)].rstrip() + "…"


def summarize(record: Record, *, grep: Pattern[str] | None = None) -> JsonObject:
    """Compact, human-scannable projection of a record: no raw body dump.

    Shows a one-line excerpt instead -- the line that matched --grep when one
    was given, else the body's first non-blank line.
    """
    body = record.get("body") or ""
    excerpt = matching_line(record, grep) if grep is not None else None
    if excerpt is None:
        excerpt = _first_nonblank_line(body)
    summary: dict[str, Any] = {
        "id": record.get("id"),
        "record_type": record.get("record_type"),
        "subject": record.get("subject"),
        "lifecycle_state": record.get("lifecycle_state"),
        "revision": record.get("revision"),
        "payload": record.get("payload"),
        "recorded_at": record.get("recorded_at"),
    }
    if "derived" in record:
        summary["derived"] = record["derived"]
    if excerpt:
        summary["body_excerpt"] = truncate(excerpt)
    return summary
