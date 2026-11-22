from __future__ import annotations

from orchestra.canon import record_payload
from orchestra.canon.types import JsonValue, Record


def question_scope(record: Record) -> str:
    scope = record_payload(record).get("scope")
    return scope if isinstance(scope, str) else ""


def question_answer_operation(
    record_type: str, record_id: str, revision: str, note: str | None
) -> dict[str, JsonValue]:
    operation: dict[str, JsonValue] = {
        "op": "update",
        "type": record_type,
        "id": record_id,
        "transition": "answered",
        "expected_revision": revision,
    }
    if note:
        operation["payload"] = {"answer": note}
    return operation
