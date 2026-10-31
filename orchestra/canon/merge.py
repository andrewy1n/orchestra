"""Merge the records of one store into another."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from orchestra.canon.backend import Backend, open_backend
from orchestra.canon.errors import StoreError
from orchestra.canon.paths import PathValidationError, validate_namespace, validate_record_type
from orchestra.canon.record import prepare_record
from orchestra.canon.revision import with_revision
from orchestra.canon.schema import SchemaSet, ref_targets
from orchestra.canon.validation import validate_store

Renames = dict[tuple[str, str], str]


class MergeError(StoreError):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.details = details or {}


def parse_namespace_map(specs: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for spec in specs:
        old, sep, new = spec.partition("=")
        if not sep:
            raise MergeError(f"--namespace expects OLD=NEW, got {spec!r}")
        try:
            validate_namespace(old)
            validate_namespace(new)
        except PathValidationError as exc:
            raise MergeError(str(exc)) from exc
        if mapping.setdefault(old, new) != new:
            raise MergeError(f"namespace {old!r} is mapped twice")
    return mapping


def parse_subject_renames(specs: list[str]) -> dict[tuple[str, str], str]:
    renames: dict[tuple[str, str], str] = {}
    for spec in specs:
        target, sep, new = spec.partition("=")
        parts = target.split(":")
        if not sep or len(parts) != 3 or not all(parts) or not new.strip() or new != new.strip():
            raise MergeError(f"--rename-subject expects NS:TYPE:OLD=NEW, got {spec!r}")
        key = (f"{parts[0]}:{parts[1]}", parts[2])
        if renames.setdefault(key, new) != new:
            raise MergeError(f"subject {parts[2]!r} of {key[0]} is renamed twice")
    return renames


def _rewrite_refs(form: dict[str, Any], value: Any, renames: Renames) -> Any:
    if "list" in form:
        if isinstance(value, list):
            return [_rewrite_refs(form["list"], item, renames) for item in value]
        return value
    if "ref" in form and not form.get("pin") and isinstance(value, str):
        for target in ref_targets(form):
            if (target, value) in renames:
                return renames[(target, value)]
    return value


class _Rewriter:
    def __init__(self, schemas: SchemaSet, namespaces: dict[str, str], renames: Renames):
        self.schemas = schemas
        self.namespaces = namespaces
        self.renames = renames
        self.revisions: dict[str, str] = {}

    def map_type(self, record_type: str) -> str:
        namespace, local = validate_record_type(record_type)
        return f"{self.namespaces.get(namespace, namespace)}:{local}"

    def record(self, record: dict[str, Any]) -> dict[str, Any]:
        out = dict(record)
        record_type = self.map_type(out["record_type"])
        out["record_type"] = record_type
        subject = (record_type, out["subject"])
        if subject in self.renames:
            out["subject"] = self.renames[subject]
        type_def = self.schemas.types.get(record_type)
        if type_def is not None and isinstance(out.get("payload"), dict):
            out["payload"] = {
                field: _rewrite_refs(type_def.fields[field], value, self.renames)
                if field in type_def.fields
                else value
                for field, value in out["payload"].items()
            }
        stamped = with_revision(prepare_record(out))
        self.revisions[record["revision"]] = stamped["revision"]
        return stamped


def _count(table: dict[str, dict[str, int]], key: str, field: str) -> None:
    row = table.setdefault(key, {"records": 0, "history": 0, "log": 0})
    row[field] += 1


def merge_store(
    target: Backend,
    schemas: SchemaSet,
    source_dir: str | Path,
    *,
    namespaces: dict[str, str] | None = None,
    subject_renames: dict[tuple[str, str], str] | None = None,
) -> dict[str, Any]:
    """Copy every record, history snapshot and op log of the source store into the target.

    Aborts before writing when an id exists in the target, when a non-event
    type and subject exists in the target, or when a mapped type is not
    declared by the target schemas. Returns a summary that includes the
    result of validating the target afterwards.
    """
    source = open_backend(Path(source_dir))
    if not source.has_record_collection():
        raise MergeError(f"{source_dir} is not a store: records/ is missing")
    if source.same_store(target):
        raise MergeError("source and target are the same store")
    namespaces = namespaces or {}
    renames: Renames = {}
    for (record_type, old), new in (subject_renames or {}).items():
        namespace, local = validate_record_type(record_type)
        renames[(f"{namespaces.get(namespace, namespace)}:{local}", old)] = new
    rewriter = _Rewriter(schemas, namespaces, renames)

    records = list(source.iter_records())
    history = list(source.read_history())
    chains = list(source.iter_chains())

    unknown = sorted(
        {
            rewriter.map_type(item["record_type"])
            for item in (*records, *history)
            if rewriter.map_type(item["record_type"]) not in schemas.types
        }
    )
    if unknown:
        raise MergeError(
            f"source types not declared by the target schemas: {unknown}",
            {"unknown_types": unknown},
        )

    existing = list(target.iter_records())
    taken = {record["id"] for record in existing}
    clashes = sorted(record["id"] for record in records if record["id"] in taken)
    if clashes:
        raise MergeError(
            f"record ids already exist in the target: {clashes}", {"id_conflicts": clashes}
        )
    occupied = {(record["record_type"], record["subject"]) for record in existing}
    subjects = sorted(
        {
            (moved["record_type"], moved["subject"])
            for moved in map(rewriter.record, records)
            if (moved["record_type"], moved["subject"]) in occupied
            and schemas.types[moved["record_type"]].lifecycle.name != "event"
        }
    )
    if subjects:
        conflicts = [{"record_type": t, "subject": s} for t, s in subjects]
        raise MergeError(
            "subjects already exist in the target (use --rename-subject): "
            + ", ".join(f"{t} {s!r}" for t, s in subjects),
            {"subject_conflicts": conflicts},
        )

    counts: dict[str, dict[str, int]] = {}
    renamed: dict[tuple[str, str, str], int] = {}
    with target.transaction():
        for snapshot in history:
            moved = rewriter.record(snapshot)
            target.archive_history(moved)
            _count(counts, moved["record_type"], "history")
        for record_id, ops in chains:
            for op in ops:
                content = {key: value for key, value in op.items() if key != "seq"}
                moved = rewriter.record(op["record"])
                content["record"] = moved
                if "conflict_revision" in content:
                    content["conflict_revision"] = rewriter.revisions.get(
                        content["conflict_revision"], content["conflict_revision"]
                    )
                target.import_op(moved["record_type"], record_id, {**content, "seq": op["seq"]})
                _count(counts, moved["record_type"], "log")
        for record in records:
            moved = rewriter.record(record)
            target.import_record(moved)
            _count(counts, moved["record_type"], "records")
            if moved["subject"] != record["subject"]:
                key = (moved["record_type"], record["subject"], moved["subject"])
                renamed[key] = renamed.get(key, 0) + 1

    errors = validate_store(schemas, backend=target)
    return {
        "types": dict(sorted(counts.items())),
        "totals": {
            field: sum(row[field] for row in counts.values())
            for field in ("records", "history", "log")
        },
        "renamed_subjects": [
            {"record_type": t, "old": old, "new": new, "records": n}
            for (t, old, new), n in sorted(renamed.items())
        ],
        "status": "invalid" if errors else "valid",
        "errors": errors,
    }
