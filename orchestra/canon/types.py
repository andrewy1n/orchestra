"""JSON values, record envelopes, and operation results."""

from __future__ import annotations

from typing import TypeAlias, TypedDict

JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


class DerivedValues(TypedDict, total=False):
    ready: bool
    wave: int | None
    referenced_by: dict[str, list[str]]
    corrected: bool


class _OptionalRecord(TypedDict, total=False):
    body: str
    time: JsonValue
    provenance: JsonValue
    derived: DerivedValues


class Record(_OptionalRecord):
    id: str
    record_type: str
    subject: str
    payload: JsonObject
    lifecycle_state: str
    relationships: dict[str, list[str]]
    revision: str
    recorded_at: str


class _OptionalOp(TypedDict, total=False):
    conflict_revision: str | None


class StoredOp(_OptionalOp):
    seq: int
    op_id: str
    kind: str
    outcome: str
    record: Record | None


class _NumberedResult(TypedDict, total=False):
    line: int


class SuccessResult(_NumberedResult):
    ok: bool
    op: str
    record: Record


class MutationResult(SuccessResult):
    predecessor: Record


class FailureResult(_NumberedResult):
    ok: bool
    op: JsonValue
    error: str
    message: str


OperationResult: TypeAlias = SuccessResult | MutationResult | FailureResult


def get_string(payload: JsonObject, key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) else None


def get_object(payload: JsonObject, key: str) -> JsonObject | None:
    value = payload.get(key)
    return value if isinstance(value, dict) else None


def get_list(payload: JsonObject, key: str) -> list[JsonValue] | None:
    value = payload.get(key)
    return value if isinstance(value, list) else None
