from __future__ import annotations

from orchestra.canon import record_payload
from orchestra.canon.types import Record


def question_scope(record: Record) -> str:
    scope = record_payload(record).get("scope")
    return scope if isinstance(scope, str) else ""
