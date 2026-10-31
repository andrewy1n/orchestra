"""Validate records and store invariants against the schema snapshots."""

from __future__ import annotations

import re
from pathlib import Path

from orchestra.canon.backend import Backend, open_backend
from orchestra.canon.errors import StoreError
from orchestra.canon.index import SUPERSEDED, RecordIndex
from orchestra.canon.schema import SchemaSet, TypeDef, ref_targets
from orchestra.canon.types import JsonObject, JsonValue, Record


class ValidationError(Exception):
    def __init__(self, message: str, code: str = "validation"):
        super().__init__(message)
        self.code = code


class TransitionError(ValidationError):
    def __init__(self, message: str, code: str = "invalid_transition"):
        super().__init__(message, code)


ENVELOPE_REQUIRED = (
    "id",
    "record_type",
    "subject",
    "lifecycle_state",
    "payload",
    "relationships",
    "recorded_at",
    "revision",
)
ENVELOPE_KEYS = frozenset(ENVELOPE_REQUIRED) | {"body", "time", "provenance"}
RELATIONSHIP_KEYS = ("supersedes", "corrects")
SUBJECT = re.compile(r"^\S+$")


def _scalar_ok(kind: JsonValue, value: JsonValue) -> bool:
    if kind == "string":
        return isinstance(value, str)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, bool)


def _describe(form: JsonObject) -> str:
    if "type" in form:
        return form["type"]  # pyright: ignore[reportReturnType]  # Schema forms are validated before value checks.
    if "enum" in form:
        return f"one of {form['enum']}"
    if "ref" in form:
        kind = "id" if form.get("pin") else "subject"
        return f"{kind} of {' or '.join(ref_targets(form))}"
    return f"list of {_describe(form['list'])}"  # pyright: ignore[reportArgumentType]  # Schema forms are validated before value checks.


def _ref_errors(schemas: SchemaSet, index: RecordIndex, form: JsonObject, value: str) -> str | None:
    targets = ref_targets(form)
    installed = [t for t in targets if t in schemas.types]
    if form.get("pin"):
        found = index.by_id.get(value)
        if found is not None and found.get("record_type") in installed:
            return None
        what = f"no {' or '.join(targets)} record with id {value!r}"
    else:
        if any(index.subject_exists(t, value) for t in installed):
            return None
        what = f"no {' or '.join(targets)} record with subject {value!r}"
    missing = [t for t in targets if t not in schemas.types]
    if missing and len(missing) == len(targets):
        return f"type {missing[0]} is not installed"
    return what


def value_errors(
    schemas: SchemaSet,
    index: RecordIndex | None,
    form: JsonObject,
    value: JsonValue,
    path: str,
    *,
    optional: bool = False,
) -> list[str]:
    if "type" in form:
        if _scalar_ok(form["type"], value):
            return []
    elif "enum" in form:
        if isinstance(value, str) and (value in form["enum"] or (value == "" and optional)):  # pyright: ignore[reportOperatorIssue]  # Schema forms are validated before value checks.
            return []
    elif "ref" in form:
        if isinstance(value, str):
            if value == "" or index is None:
                return []
            problem = _ref_errors(schemas, index, form, value)
            return [f"{path}: {problem}"] if problem else []
    else:
        if isinstance(value, list):
            errors: list[str] = []
            for position, item in enumerate(value):
                errors.extend(
                    value_errors(schemas, index, form["list"], item, f"{path}[{position}]")  # pyright: ignore[reportArgumentType]  # Schema forms are validated before value checks.
                )
            return errors
    return [f"{path}: expected {_describe(form)}, got {value!r}"]


def payload_errors(
    schemas: SchemaSet, index: RecordIndex | None, type_def: TypeDef, record: Record | JsonObject
) -> list[str]:
    payload = record.get("payload")
    label = record["id"]
    if not isinstance(payload, dict):
        return [f"{label}: payload must be an object"]
    errors: list[str] = []
    for key in payload:
        if key not in type_def.fields:
            errors.append(
                f"{label}: payload field {key!r} is not declared by {type_def.record_type}"
            )
    for field, form in type_def.fields.items():
        if field not in payload:
            if not form.get("optional"):
                errors.append(f"{label}: missing payload field {field!r}")
            continue
        errors.extend(
            f"{label}: payload field {message}"
            for message in value_errors(
                schemas,
                index,
                form,
                payload[field],
                repr(field),
                optional=bool(form.get("optional")),
            )
        )
    return errors


def section_errors(type_def: TypeDef, record: Record | JsonObject) -> list[str]:
    if not type_def.sections:
        return []
    errors: list[str] = []
    sections = _body_sections(record.get("body") or "")  # pyright: ignore[reportArgumentType]  # Raw JSON envelopes are checked at ingress.
    for name in type_def.sections:
        content = sections.get(name)
        if content is None:
            errors.append(f"{record['id']}: missing required section {name!r}")
        elif not content.strip():
            errors.append(f"{record['id']}: required section {name!r} is empty")
    return errors


def relationship_errors(
    type_def: TypeDef, index: RecordIndex | None, record: Record | JsonObject
) -> list[str]:
    label = record["id"]
    relationships = record.get("relationships")
    if not isinstance(relationships, dict):
        return [f"{label}: relationships must be an object"]
    allowed = {
        "supersedes": type_def.lifecycle.supersedable,
        "corrects": type_def.lifecycle.appends_only,
    }
    errors: list[str] = []
    for rel_type, targets in relationships.items():
        if rel_type not in RELATIONSHIP_KEYS or not allowed[rel_type]:
            errors.append(f"{label}: unknown relationship {rel_type!r}")
            continue
        if not isinstance(targets, list) or not all(isinstance(t, str) for t in targets):
            errors.append(f"{label}: relationship {rel_type} must be a list of record ids")
            continue
        for target in targets:
            if index is not None and target not in index.by_id:
                errors.append(f"{label}: unknown relationship target {target!r}")
    return errors


def record_errors(
    schemas: SchemaSet, record: Record | JsonObject, index: RecordIndex | None
) -> list[str]:
    label = record.get("id", "<record>")
    missing = [key for key in ENVELOPE_REQUIRED if key not in record]
    if missing:
        return [f"{label}: missing required fields {missing}"]
    unknown = sorted(set(record) - ENVELOPE_KEYS)
    if unknown:
        return [f"{label}: unknown envelope keys {unknown}"]
    record_type = record["record_type"]
    if record_type not in schemas.types:  # pyright: ignore[reportArgumentType]  # Preserve native errors for malformed unhashable record types.
        return [f"{label}: unknown record type {record_type!r}"]
    type_def = schemas.types[record_type]  # pyright: ignore[reportArgumentType]  # The membership check above establishes the schema key.
    errors: list[str] = []
    if not isinstance(record["subject"], str) or not SUBJECT.match(record["subject"]):
        errors.append(f"{label}: subject must be a non-empty slug")
    if record["lifecycle_state"] not in type_def.lifecycle.states:  # pyright: ignore[reportArgumentType]  # Preserve native membership errors for malformed JSON values.
        errors.append(f"{label}: invalid lifecycle state {record['lifecycle_state']!r}")
    errors.extend(payload_errors(schemas, index, type_def, record))
    errors.extend(relationship_errors(type_def, index, record))
    errors.extend(section_errors(type_def, record))
    return errors


def validate_record(
    schemas: SchemaSet, record: Record | JsonObject, index: RecordIndex | None = None
) -> None:
    errors = record_errors(schemas, record, index)
    if errors:
        raise ValidationError("; ".join(errors))


_SECTION_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")


def _body_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in (body or "").splitlines():
        match = _SECTION_HEADING_RE.match(line)
        if match:
            heading: str = match.group(1)
            current = heading
            sections.setdefault(heading, [])
            continue
        if current is not None:
            sections[current].append(line)
    return {name: "\n".join(lines) for name, lines in sections.items()}


def _supersede_errors(
    records: list[Record], schemas: SchemaSet, index: RecordIndex, errors: list[str]
) -> None:
    successors: dict[str, list[Record]] = {}
    for record in records:
        for target_id in (record.get("relationships") or {}).get("supersedes") or []:
            successors.setdefault(target_id, []).append(record)
            target = index.by_id.get(target_id)
            if target is None:
                errors.append(f"{record['id']}: relationship target {target_id} missing")
            elif target["record_type"] != record["record_type"]:
                errors.append(f"{record['id']}: supersedes target {target_id} has different type")
            elif target["lifecycle_state"] != SUPERSEDED:
                errors.append(f"{record['id']}: supersedes target {target_id} not superseded")
            elif target["subject"] != record["subject"]:
                errors.append(
                    f"{record['id']}: supersedes successor breaks subject continuity with {target_id}"
                )
    for record in records:
        if record.get("lifecycle_state") != SUPERSEDED:
            continue
        found = successors.get(record["id"], [])
        if len(found) != 1:
            errors.append(
                f"{record['id']}: superseded record requires exactly one same-type successor, "
                f"found {len(found)}"
            )


def _correct_errors(records: list[Record], index: RecordIndex, errors: list[str]) -> None:
    correctors: dict[str, list[str]] = {}
    for record in records:
        for target_id in (record.get("relationships") or {}).get("corrects") or []:
            target = index.by_id.get(target_id)
            if target is None:
                errors.append(f"{record['id']}: corrects target {target_id} missing")
                continue
            if target["record_type"] != record["record_type"]:
                errors.append(f"{record['id']}: corrects target {target_id} has different type")
            correctors.setdefault(target_id, []).append(record["id"])
    for target_id, ids in correctors.items():
        if len(ids) != 1:
            errors.append(
                f"{target_id}: occurrence requires exactly one correcting successor, found {len(ids)}"
            )


def _current_errors(records: list[Record], schemas: SchemaSet, errors: list[str]) -> None:
    active: dict[tuple[str, str], str] = {}
    for record in records:
        type_def = schemas.types.get(record.get("record_type", ""))
        if type_def is None or type_def.lifecycle.name != "current":
            continue
        if record.get("lifecycle_state") != type_def.lifecycle.initial:
            continue
        key = (record["record_type"], record["subject"])
        if key in active:
            errors.append(
                f"multiple active {key[0]} for subject={key[1]!r}: {active[key]} and {record['id']}"
            )
        else:
            active[key] = record["id"]


def validate_append_only_history(
    backend: Backend, records: list[Record], schemas: SchemaSet, errors: list[str]
) -> None:
    for record in records:
        type_def = schemas.types.get(record.get("record_type", ""))
        if type_def is None or not type_def.lifecycle.appends_only:
            continue
        try:
            exists = backend.history_exists(record["record_type"], record["id"], record["revision"])
        except (ValueError, StoreError) as exc:
            errors.append(f"{record['id']}: invalid append-only history path: {exc}")
            continue
        if not exists:
            errors.append(f"{record['id']}: event record missing create audit snapshot")


def validate_store(
    schemas: SchemaSet,
    records: list[Record] | None = None,
    *,
    store_root: Path | None = None,
    immutability: bool = True,
    backend: Backend | None = None,
) -> list[str]:
    errors: list[str] = []
    if backend is None and store_root is not None:
        backend = open_backend(store_root)
    if records is None and backend is not None:
        records = list(backend.iter_records(errors=errors))
    records = records or []
    index = RecordIndex(records)
    for record in records:
        errors.extend(record_errors(schemas, record, index))
    _current_errors(records, schemas, errors)
    _supersede_errors(records, schemas, index, errors)
    _correct_errors(records, index, errors)
    if backend is not None:
        backend.check_integrity(errors, immutability=immutability)
        validate_append_only_history(backend, records, schemas, errors)
    return errors


def check_transition(type_def: TypeDef, src: str, dest: object) -> None:
    if not type_def.lifecycle.allows(src, dest):
        raise TransitionError(f"invalid transition {src!r} -> {dest!r}")


def reject_supersede_via_update(type_def: TypeDef, dest: object) -> None:
    if dest == SUPERSEDED:
        raise TransitionError(
            "transition to superseded requires the supersede operation", "use_supersede"
        )


def reject_event_mutation(type_def: TypeDef) -> None:
    if type_def.lifecycle.appends_only:
        raise TransitionError("event records cannot be mutated; correct them", "append_only")
