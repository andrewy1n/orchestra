"""Git-backed typed record store."""

from __future__ import annotations

from typing import Any

__version__ = "0.1.0"


def record_payload(record: dict[str, Any]) -> dict[str, Any]:
    payload = record.get("payload")
    return payload if isinstance(payload, dict) else {}
