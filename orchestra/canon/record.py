"""Build a new record dict from a type definition.

Command code and Project both import this module. It does not import the CLI.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from orchestra.canon.schema import TypeDef


def normalize_body(body: str) -> str:
    if not body:
        return ""
    lines = [line.rstrip() for line in body.split("\n")]
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n" if lines else ""


def prepare_record(record: dict[str, Any]) -> dict[str, Any]:
    out = dict(record)
    out["body"] = normalize_body(out.get("body", ""))
    return out


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def base_record(
    type_def: TypeDef,
    *,
    subject: str,
    payload: dict[str, Any],
    record_id: str,
    lifecycle_state: str | None = None,
    relationships: dict[str, list[str]] | None = None,
    body: str = "",
    time: Any = None,
    provenance: Any = None,
    recorded_at: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "id": record_id,
        "record_type": type_def.record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": lifecycle_state or type_def.lifecycle.initial,
        "relationships": relationships or {},
        "revision": "",
        "body": body,
        "recorded_at": recorded_at or now(),
    }
    if time is not None:
        record["time"] = time
    if provenance is not None:
        record["provenance"] = provenance
    return record
