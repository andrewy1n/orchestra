"""Validate records and store invariants against the schema snapshots."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from orchestra.canon.index import SUPERSEDED, RecordIndex
from orchestra.canon.oplog import fold, read_ops
from orchestra.canon.paths import revision_filename, type_dir_name
from orchestra.canon.record_file import RECORD_GLOB, RECORD_SUFFIX, RecordFileError, load_record
from orchestra.canon.revision import compute_revision
from orchestra.canon.schema import SchemaSet, TypeDef, ref_targets


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


def _scalar_ok(kind: str, value: Any) -> bool:
    if kind == "string":
        return isinstance(value, str)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, bool)


def _describe(form: dict[str, Any]) -> str:
    if "type" in form:
        return form["type"]
    if "enum" in form:
        return f"one of {form['enum']}"
    if "ref" in form:
        kind = "id" if form.get("pin") else "subject"
        return f"{kind} of {' or '.join(ref_targets(form))}"
    return f"list of {_describe(form['list'])}"


def _ref_errors(
    schemas: SchemaSet, index: RecordIndex, form: dict[str, Any], value: str
) -> str | None:
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
    form: dict[str, Any],
    value: Any,
    path: str,
    *,
    optional: bool = False,
) -> list[str]:
    if "type" in form:
        if _scalar_ok(form["type"], value):
            return []
    elif "enum" in form:
        if isinstance(value, str) and (value in form["enum"] or (value == "" and optional)):
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
                errors.extend(value_errors(schemas, index, form["list"], item, f"{path}[{position}]"))
            return errors
    return [f"{path}: expected {_describe(form)}, got {value!r}"]


def payload_errors(
    schemas: SchemaSet, index: RecordIndex | None, type_def: TypeDef, record: dict[str, Any]
) -> list[str]:
    payload = record.get("payload")
    label = record["id"]
    if not isinstance(payload, dict):
        return [f"{label}: payload must be an object"]
    errors: list[str] = []
    for key in payload:
        if key not in type_def.fields:
            errors.append(f"{label}: payload field {key!r} is not declared by {type_def.record_type}")
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


def section_errors(type_def: TypeDef, record: dict[str, Any]) -> list[str]:
    if not type_def.sections:
        return []
    errors: list[str] = []
    sections = _body_sections(record.get("body") or "")
    for name in type_def.sections:
        content = sections.get(name)
        if content is None:
            errors.append(f"{record['id']}: missing required section {name!r}")
        elif not content.strip():
            errors.append(f"{record['id']}: required section {name!r} is empty")
    return errors


def relationship_errors(
    type_def: TypeDef, index: RecordIndex | None, record: dict[str, Any]
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
    schemas: SchemaSet, record: dict[str, Any], index: RecordIndex | None
) -> list[str]:
    label = record.get("id", "<record>")
    missing = [key for key in ENVELOPE_REQUIRED if key not in record]
    if missing:
        return [f"{label}: missing required fields {missing}"]
    unknown = sorted(set(record) - ENVELOPE_KEYS)
    if unknown:
        return [f"{label}: unknown envelope keys {unknown}"]
    record_type = record["record_type"]
    if record_type not in schemas.types:
        return [f"{label}: unknown record type {record_type!r}"]
    type_def = schemas.types[record_type]
    errors: list[str] = []
    if not isinstance(record["subject"], str) or not SUBJECT.match(record["subject"]):
        errors.append(f"{label}: subject must be a non-empty slug")
    if record["lifecycle_state"] not in type_def.lifecycle.states:
        errors.append(f"{label}: invalid lifecycle state {record['lifecycle_state']!r}")
    errors.extend(payload_errors(schemas, index, type_def, record))
    errors.extend(relationship_errors(type_def, index, record))
    errors.extend(section_errors(type_def, record))
    return errors


def validate_record(
    schemas: SchemaSet, record: dict[str, Any], index: RecordIndex | None = None
) -> None:
    errors = record_errors(schemas, record, index)
    if errors:
        raise ValidationError("; ".join(errors))


def _validate_history_path_layout(path: Path, history_root: Path, snapshot: dict[str, Any], errors: list[str]) -> None:
    try:
        rel = path.relative_to(history_root)
    except ValueError:
        errors.append(f"history snapshot outside history root: {path}")
        return
    parts = rel.parts
    if len(parts) != 3:
        errors.append(f"history snapshot bad layout: {path}")
        return
    type_dir, record_id, filename = parts
    record_type = snapshot.get("record_type")
    snapshot_id = snapshot.get("id")
    revision = snapshot.get("revision")
    if not record_type or not snapshot_id or not revision:
        errors.append(f"history snapshot missing type/id/revision: {path}")
        return
    try:
        expected_type_dir = type_dir_name(record_type)
        expected_filename = revision_filename(revision)
    except ValueError as exc:
        errors.append(f"history snapshot invalid path fields: {path}: {exc}")
        return
    if type_dir != expected_type_dir:
        errors.append(
            f"history snapshot type directory mismatch: {path} expected {expected_type_dir!r}"
        )
    if record_id != snapshot_id:
        errors.append(
            f"history snapshot record id mismatch: {path} expected parent {snapshot_id!r}"
        )
    if filename != expected_filename:
        errors.append(
            f"history snapshot revision filename mismatch: {path} expected {expected_filename!r}"
        )


def validate_history(store_root: Path, records: list[dict[str, Any]], errors: list[str]) -> None:
    history_root = store_root / "history"
    if not history_root.is_dir():
        return
    known_ids = {record["id"] for record in records}
    for path in sorted(history_root.rglob(RECORD_GLOB)):
        try:
            snapshot = load_record(path.read_text(), path)
        except RecordFileError as exc:
            errors.append(f"history malformed record file {path}: {exc}")
            continue
        if not isinstance(snapshot, dict):
            errors.append(f"history snapshot must be a record object: {path}")
            continue
        if snapshot.get("revision") != compute_revision(snapshot):
            errors.append(f"history tamper detected: {path}")
            continue
        _validate_history_path_layout(path, history_root, snapshot, errors)
        record_id = snapshot.get("id")
        record_type = snapshot.get("record_type")
        if record_id not in known_ids:
            errors.append(f"history snapshot {path.name}: unknown record id {record_id!r}")
        if record_type and record_id:
            expected = (
                store_root
                / "records"
                / type_dir_name(record_type)
                / f"{record_id}{RECORD_SUFFIX}"
            )
            if not expected.is_file():
                errors.append(f"history snapshot {path.name}: no live record for {record_id}")


def _run_git(args: list[str]) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(args, capture_output=True, text=True)
    except OSError:
        return None


def _git_toplevel(path: Path) -> Path | None:
    result = _run_git(["git", "-C", str(path), "rev-parse", "--show-toplevel"])
    if result is None or result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def _git_head_exists(repo_root: Path) -> bool:
    result = _run_git(["git", "-C", str(repo_root), "rev-parse", "--verify", "-q", "HEAD"])
    return result is not None and result.returncode == 0


def _authorized_record_rewrite(store_root: Path, records_rel: str, offending: str) -> bool:
    """True when a modified `records/` path is a rewrite the store's own op
    log can account for, not an out-of-band edit.

    `oplog.append_resolved_op` bakes the exact record dict into every
    accepted create/write op, and `Store._materialize` always writes
    `dump_record(fold(read_ops(chain_dir)))` -- the chain's folded state --
    to the record path (see `store.py`). So if the record currently on disk
    equals that fold, some accepted op in *this record's own chain*
    produced it, whether or not that op or the record file has been
    committed yet. Nothing here needs the record file, or the op that
    produced it, to be committed -- only that they agree with each other.

    Deliberately does not accept a bare "revision is self-consistent"
    record: `revision` is a public, deterministic hash of the record's own
    content (see `revision.py`), so a hand-edited record paired with a
    hand-recomputed revision proves nothing.

    What this catches is an edit made without going through the runtime --
    the realistic case, an agent or a person fixing a record file by hand.
    It is not proof of authorship: ops are unsigned JSON, so an edit that
    also appends a matching op to the chain passes. Treat it as a
    consistency check between a record and its own log, not as tamper
    evidence; `git diff` remains the thing that shows a reader what changed.
    """
    prefix = f"{records_rel}/"
    if not offending.startswith(prefix):
        return False
    parts = offending[len(prefix) :].split("/")
    if len(parts) != 2:
        return False
    type_dir, filename = parts
    if not filename.endswith(RECORD_SUFFIX):
        return False
    record_id = filename[: -len(RECORD_SUFFIX)]
    path = store_root / "records" / type_dir / filename
    try:
        text = path.read_text()
    except OSError:
        return False
    try:
        record = load_record(text, path)
    except RecordFileError:
        return False
    if not isinstance(record, dict):
        return False
    if record.get("id") != record_id:
        return False
    record_type = record.get("record_type")
    if not isinstance(record_type, str):
        return False
    try:
        expected_type_dir = type_dir_name(record_type)
    except ValueError:
        return False
    if expected_type_dir != type_dir:
        return False
    chain_dir = store_root / "log" / type_dir / record_id
    return fold(read_ops(chain_dir)) == record


def validate_immutability(store_root: Path, errors: list[str]) -> None:
    """Fail on any store path that exists in git HEAD but was changed or removed
    in the working tree. Supersede is the only sanctioned mutation path, and it
    always writes a new record id -- so any in-place change to a path git already
    committed is a violation by construction, unless the op log accounts for it
    (see `_authorized_record_rewrite`). New, uncommitted paths are fine.

    History snapshots (`Store.archive_history`/`Store.iter_history`) are
    write-once, so a committed snapshot changing at all is a tamper by the same
    rule as a record file. `config.json` and `schemas/` change whenever
    `schemas sync` runs, so they are exempt.
    """
    if not store_root.exists():
        return
    repo_root = _git_toplevel(store_root)
    if repo_root is None:
        return
    if not _git_head_exists(repo_root):
        return
    try:
        rel = store_root.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return
    config_rel = (rel / "config.json").as_posix()
    schemas_rel = (rel / "schemas").as_posix() + "/"
    records_rel = (rel / "records").as_posix()
    result = _run_git(
        ["git", "-C", str(repo_root), "diff", "--name-status", "HEAD", "--", rel.as_posix()]
    )
    if result is None or result.returncode != 0:
        return
    for line in result.stdout.splitlines():
        line = line.rstrip("\n")
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("A"):
            continue
        offending = parts[1] if len(parts) > 1 else line
        if offending == config_rel or offending.startswith(schemas_rel):
            continue
        if not status.startswith("D") and _authorized_record_rewrite(
            store_root, records_rel, offending
        ):
            continue
        errors.append(
            f"immutability violation: committed store path modified or deleted "
            f"(git status {status}): {offending}"
        )


def load_records_for_validation(store_root: Path, errors: list[str]) -> list[dict[str, Any]]:
    records_dir = store_root / "records"
    if not records_dir.is_dir():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(records_dir.rglob("*")):
        # Skipping these quietly would validate an unmigrated store as clean.
        if path.is_file() and path.suffix != RECORD_SUFFIX:
            errors.append(f"unrecognized record file (expected {RECORD_SUFFIX}): {path}")
    for path in sorted(records_dir.rglob(RECORD_GLOB)):
        try:
            record = load_record(path.read_text(), path)
        except RecordFileError as exc:
            errors.append(f"record malformed record file {path}: {exc}")
            continue
        if not isinstance(record, dict):
            errors.append(f"record file must be a record object: {path}")
            continue
        if record.get("revision") != compute_revision(record):
            errors.append(f"record revision tamper detected: {path}")
            continue
        records.append(record)
    return records


_SECTION_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")


def _body_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in (body or "").splitlines():
        match = _SECTION_HEADING_RE.match(line)
        if match:
            current = match.group(1)
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    return {name: "\n".join(lines) for name, lines in sections.items()}


def _supersede_errors(
    records: list[dict[str, Any]], schemas: SchemaSet, index: RecordIndex, errors: list[str]
) -> None:
    successors: dict[str, list[dict[str, Any]]] = {}
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


def _correct_errors(records: list[dict[str, Any]], index: RecordIndex, errors: list[str]) -> None:
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


def _current_errors(records: list[dict[str, Any]], schemas: SchemaSet, errors: list[str]) -> None:
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
    store_root: Path, records: list[dict[str, Any]], schemas: SchemaSet, errors: list[str]
) -> None:
    for record in records:
        type_def = schemas.types.get(record.get("record_type", ""))
        if type_def is None or not type_def.lifecycle.appends_only:
            continue
        try:
            path = (
                store_root
                / "history"
                / type_dir_name(record["record_type"])
                / record["id"]
                / revision_filename(record["revision"])
            )
        except ValueError as exc:
            errors.append(f"{record['id']}: invalid append-only history path: {exc}")
            continue
        if not path.is_file():
            errors.append(f"{record['id']}: event record missing create audit snapshot")


def validate_store(
    schemas: SchemaSet,
    records: list[dict[str, Any]] | None = None,
    *,
    store_root: Path | None = None,
    immutability: bool = True,
) -> list[str]:
    errors: list[str] = []
    if records is None and store_root is not None:
        records = load_records_for_validation(store_root, errors)
    records = records or []
    index = RecordIndex(records)
    for record in records:
        errors.extend(record_errors(schemas, record, index))
    _current_errors(records, schemas, errors)
    _supersede_errors(records, schemas, index, errors)
    _correct_errors(records, index, errors)
    if store_root is not None:
        validate_history(store_root, records, errors)
        validate_append_only_history(store_root, records, schemas, errors)
        if immutability:
            validate_immutability(store_root, errors)
    return errors


def check_transition(type_def: TypeDef, src: str, dest: str) -> None:
    if not type_def.lifecycle.allows(src, dest):
        raise TransitionError(f"invalid transition {src!r} -> {dest!r}")


def reject_supersede_via_update(type_def: TypeDef, dest: str) -> None:
    if dest == SUPERSEDED:
        raise TransitionError("transition to superseded requires the supersede operation", "use_supersede")


def reject_event_mutation(type_def: TypeDef) -> None:
    if type_def.lifecycle.appends_only:
        raise TransitionError("event records cannot be mutated; correct them", "append_only")
