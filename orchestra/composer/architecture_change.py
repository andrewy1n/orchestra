from __future__ import annotations

import ast
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from importlib.util import resolve_name
from pathlib import Path, PurePosixPath

from orchestra.canon.errors import RecordShapeError, StoreError
from orchestra.canon.fields import optional_text, optional_text_list
from orchestra.canon.project import Project
from orchestra.canon.sections import body_section
from orchestra.canon.types import JsonObject, Record
from orchestra.composer.records import (
    ARCHITECTURE_DECISION,
    COMPONENT,
    INTERFACE,
    read_architecture_decision,
    read_component,
)
from orchestra.score.lookups import direct_corrected_ids, latest_record
from orchestra.score.planning.standing_constraint import RECORD_TYPE as STANDING_CONSTRAINT
from orchestra.score.planning.standing_constraint import is_current_constraint
from orchestra.tools import Git

ARCHITECTURE_PROPOSAL = "composer:architecture-proposal"
CONSTRAINT_CHANGE = "composer:constraint-change"


@dataclass(frozen=True)
class RecordPin:
    id: str
    revision: str


@dataclass(frozen=True)
class ConstraintChange:
    record: Record
    operation: str
    subject: str
    base: RecordPin | None
    payload: JsonObject
    basis: str


@dataclass(frozen=True)
class ArchitectureProposal:
    record: Record
    phase: str
    status: str
    adr: str
    affects: tuple[str, ...]
    enforced_by: tuple[str, ...]
    rationale: str
    base_adr: RecordPin | None
    constraints: tuple[ConstraintChange, ...]


def _text(record: Record, field: str) -> str:
    value = optional_text(record, record["payload"], field)
    if value is None or not value.strip():
        raise RecordShapeError(record["id"], field, "requires non-empty text")
    return value


def _section(record: Record, heading: str) -> str:
    value = body_section(record.get("body", ""), heading)
    if not value:
        raise RecordShapeError(record["id"], "body", f"requires a non-empty {heading} section")
    return value


def _pin(
    record: Record,
    field: str,
    record_type: str,
    subject: str,
    by_id: dict[str, Record],
) -> RecordPin | None:
    fields = record["payload"]
    target = optional_text(record, fields, field)
    revision = optional_text(record, fields, f"{field}_revision")
    if target is None and revision is None:
        return None
    source = by_id.get(target) if target is not None else None
    if (
        source is None
        or source["record_type"] != record_type
        or source["subject"] != subject
        or target is None
        or revision is None
    ):
        raise RecordShapeError(
            record["id"], field, "requires a record id and revision for the target"
        )
    return RecordPin(target, revision)


def _read_constraint_change(record: Record, by_id: dict[str, Record]) -> ConstraintChange:
    fields = record["payload"]
    subject = _text(record, "constraint")
    operation = _text(record, "operation")
    base = _pin(record, "base_constraint", STANDING_CONSTRAINT, subject, by_id)
    payload: JsonObject = {}
    if operation in ("add", "revise"):
        payload = {field: _text(record, field) for field in ("area", "rule", "check")}
        payload["targets"] = list(optional_text_list(record, fields, "targets"))
    elif operation != "retire":
        raise RecordShapeError(record["id"], "operation", "requires add, revise, or retire")
    if (operation == "add") != (base is None):
        raise RecordShapeError(
            record["id"], "base_constraint", "revision and retirement require a baseline"
        )
    return ConstraintChange(record, operation, subject, base, payload, _section(record, "Basis"))


def proposal_for_phase(records: Sequence[Record], phase: str) -> ArchitectureProposal | None:
    active = [
        record
        for record in records
        if record["record_type"] == ARCHITECTURE_PROPOSAL
        and record["lifecycle_state"] == "active"
        and record["payload"].get("phase") == phase
    ]
    if not active:
        return None
    record = active[0]
    if len(active) > 1:
        raise RecordShapeError(record["id"], "phase", "requires a single proposal per phase")
    fields = record["payload"]
    status = _text(record, "status")
    if status not in ("pending", "withdrawn"):
        raise RecordShapeError(record["id"], "status", "requires pending or withdrawn")
    adr = _text(record, "adr")
    affects = optional_text_list(record, fields, "affects")
    if not affects:
        raise RecordShapeError(
            record["id"], "affects", "requires at least one component or interface"
        )
    by_id = {item["id"]: item for item in records}
    changes: list[ConstraintChange] = []
    for change_id in optional_text_list(record, fields, "constraints"):
        change = by_id.get(change_id)
        if change is None or change["record_type"] != CONSTRAINT_CHANGE:
            raise RecordShapeError(
                record["id"], "constraints", f"missing constraint change {change_id}"
            )
        changes.append(_read_constraint_change(change, by_id))
    if len({change.subject for change in changes}) != len(changes):
        raise RecordShapeError(
            record["id"], "constraints", "requires at most one change per constraint"
        )
    return ArchitectureProposal(
        record=record,
        phase=phase,
        status=status,
        adr=adr,
        affects=affects,
        enforced_by=optional_text_list(record, fields, "enforced_by"),
        rationale=_section(record, "Rationale"),
        base_adr=_pin(record, "base_adr", ARCHITECTURE_DECISION, adr, by_id),
        constraints=tuple(changes),
    )


APPROVAL = "composer:architecture-approval"
RECONCILIATION = "composer:architecture-reconciliation"


def _approved(
    records: Sequence[Record], proposal: ArchitectureProposal, candidate: str
) -> Record | None:
    corrected = direct_corrected_ids(records)
    return latest_record(
        record
        for record in records
        if record["record_type"] == APPROVAL
        and record["id"] not in corrected
        and record["payload"]["proposal"] == proposal.record["id"]
        and record["payload"]["proposal_revision"] == proposal.record["revision"]
        and record["payload"]["candidate"] == candidate
        and str(record["payload"]["approved_by"]).strip()
    )


def _operation(
    current: dict[tuple[str, str], Record],
    record_type: str,
    subject: str,
    base: RecordPin | None,
    payload: JsonObject,
    body: str,
) -> JsonObject:
    record = current.get((record_type, subject))
    if base is None and record is None:
        return {
            "op": "create",
            "type": record_type,
            "subject": subject,
            "payload": payload,
            "body": body,
        }
    if (
        base is None
        or record is None
        or (base.id, base.revision) != (record["id"], record["revision"])
    ):
        raise StoreError(
            f"Architecture change for {subject!r} requires refreshed review of its current version."
        )
    return {
        "op": "supersede",
        "type": record_type,
        "id": base.id,
        "expected_revision": base.revision,
        "payload": payload,
        "body": body,
    }


def _changes(records: Sequence[Record], proposal: ArchitectureProposal) -> list[JsonObject]:
    current = {
        (record["record_type"], record["subject"]): record
        for record in records
        if record["lifecycle_state"] == "active"
    }
    targets = {subject for kind, subject in current if kind in (COMPONENT, INTERFACE)}
    missing_targets = set(proposal.affects) - targets
    if missing_targets:
        raise StoreError(
            f"Architecture proposal requires refreshed review of targets {sorted(missing_targets)}."
        )
    active_constraints = {
        record["subject"] for record in current.values() if is_current_constraint(record)
    }
    retirements = {
        change.subject for change in proposal.constraints if change.operation == "retire"
    }
    if retirements:
        for (kind, subject), record in sorted(current.items()):
            if kind != ARCHITECTURE_DECISION or subject == proposal.adr:
                continue
            decision = read_architecture_decision(record)
            orphaned = retirements.intersection(decision.enforced_by)
            if decision.status == "accepted" and orphaned:
                raise StoreError(
                    f"Cannot retire {', '.join(sorted(orphaned))}. Accepted ADR {subject!r} still depends on it."
                )
    operations: list[JsonObject] = []
    for change in proposal.constraints:
        payload = {**change.payload, "retired": change.operation == "retire"}
        if change.operation == "retire":
            active_constraints.discard(change.subject)
        else:
            active_constraints.add(change.subject)
        operations.append(
            _operation(
                current,
                STANDING_CONSTRAINT,
                change.subject,
                change.base,
                payload,
                f"## Basis\n\n{change.basis}\n",
            )
        )
    missing_constraints = set(proposal.enforced_by) - active_constraints
    if missing_constraints:
        raise StoreError(
            f"Architecture proposal requires refreshed review of constraints {sorted(missing_constraints)}."
        )
    operations.append(
        _operation(
            current,
            ARCHITECTURE_DECISION,
            proposal.adr,
            proposal.base_adr,
            {
                "status": "accepted",
                "affects": [*proposal.affects],
                "enforced_by": [*proposal.enforced_by],
            },
            f"## Rationale\n\n{proposal.rationale}\n",
        )
    )
    return operations


def reconcile_architecture(project: Project, phase: str, candidate: str) -> bool:
    token = project.change_token()
    records = project.records()
    if any(
        record["record_type"] == RECONCILIATION and record["subject"] == phase for record in records
    ):
        return False
    proposal = proposal_for_phase(records, phase)
    if proposal is None or proposal.status == "withdrawn":
        return False
    approval = _approved(records, proposal, candidate)
    if approval is None:
        record = proposal.record
        raise StoreError(
            f"Architecture proposal {record['id']} at {record['revision']} is pending without "
            f"approval for candidate {candidate}. Approve that proposal and candidate or withdraw "
            "the proposal before closing the phase."
        )
    operations = _changes(records, proposal)
    operations.append(
        {
            "op": "create",
            "type": RECONCILIATION,
            "subject": phase,
            "payload": {"approval": approval["id"]},
        }
    )
    project.apply_at_snapshot(operations, token)
    return True


Edge = tuple[str, str]


def proposed_constraint(records: Sequence[Record], phase: str, change_id: str) -> Record | None:
    proposal = proposal_for_phase(records, phase)
    if proposal is None or proposal.status != "pending":
        return None
    return next(
        (
            change.record
            for change in proposal.constraints
            if change.record["id"] == change_id and change.operation != "retire"
        ),
        None,
    )


def _prefixes(records: Sequence[Record]) -> dict[str, str]:
    prefixes: dict[str, str] = {}
    for record in records:
        if record["record_type"] != COMPONENT or record["lifecycle_state"] != "active":
            continue
        component = read_component(record)
        for prefix in component.module_prefixes:
            if prefix in prefixes and prefixes[prefix] != record["subject"]:
                raise ValueError(f"Multiple components declare module prefix {prefix!r}.")
            prefixes[prefix] = record["subject"]
    return prefixes


def _component(module: str, prefixes: dict[str, str]) -> str | None:
    while module:
        if module in prefixes:
            return prefixes[module]
        module = module.rpartition(".")[0]
    return None


def _imports(tree: ast.Module, package: str) -> Iterator[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                try:
                    module = resolve_name("." * node.level + module, package)
                except ImportError as error:
                    raise ValueError(str(error)) from error
            if module:
                yield from (
                    module if alias.name == "*" else f"{module}.{alias.name}"
                    for alias in node.names
                )


@dataclass(frozen=True)
class DependencyChanges:
    baseline: str
    candidate: str
    added: tuple[Edge, ...]
    removed: tuple[Edge, ...]
    unmapped: tuple[str, ...]
    has_mappings: bool


def _snapshot(
    git: Git, revision: str, prefixes: dict[str, str]
) -> tuple[dict[str, tuple[str, str, str]], set[str]]:
    modules: dict[str, tuple[str, str, str]] = {}
    unmapped: set[str] = set()
    for entry in git.text("ls-tree", "-r", "-z", revision).split("\0"):
        metadata, _, name = entry.partition("\t")
        if not name.endswith(".py") or not metadata.startswith(("100644 blob ", "100755 blob ")):
            continue
        path = PurePosixPath(name)
        parts = path.with_suffix("").parts
        if parts[0] == "src" and _component(".".join(parts), prefixes) is None:
            parts = parts[1:]
        package = ".".join(parts[:-1])
        module = package if path.stem == "__init__" else ".".join(parts)
        owner = _component(module, prefixes)
        if owner is None:
            unmapped.add(module or name)
        else:
            modules[name] = (metadata.rsplit(" ", 1)[-1], package, owner)
    return modules, unmapped


def _edges(
    modules: dict[str, tuple[str, str, str]],
    blobs: dict[str, bytes],
    revision: str,
    prefixes: dict[str, str],
) -> set[Edge]:
    edges: set[Edge] = set()
    for name, (blob, package, source) in modules.items():
        try:
            tree = ast.parse(blobs[blob], filename=name)
            for target in _imports(tree, package):
                owner = _component(target, prefixes)
                if owner is not None and owner != source:
                    edges.add((source, owner))
        except (SyntaxError, ValueError) as error:
            raise ValueError(f"Cannot analyze imports in {name} at {revision}: {error}") from error
    return edges


def dependency_changes(
    records: Sequence[Record], work: Path, base: str, head: str
) -> DependencyChanges:
    git = Git(work)
    baseline, candidate = git.resolve(base), git.resolve(head)
    if baseline is None or candidate is None:
        raise ValueError("Architecture review requires a resolvable base and candidate commit.")
    prefixes = _prefixes(records)
    if not prefixes:
        return DependencyChanges(baseline, candidate, (), (), (), False)
    before, old_unmapped = _snapshot(git, baseline, prefixes)
    after, new_unmapped = _snapshot(git, candidate, prefixes)
    blobs = git.read_blobs(
        tuple(dict.fromkeys(row[0] for row in (*before.values(), *after.values())))
    )
    old_edges = _edges(before, blobs, baseline, prefixes)
    new_edges = _edges(after, blobs, candidate, prefixes)
    return DependencyChanges(
        baseline,
        candidate,
        tuple(sorted(new_edges - old_edges)),
        tuple(sorted(old_edges - new_edges)),
        tuple(sorted(old_unmapped | new_unmapped)),
        True,
    )
