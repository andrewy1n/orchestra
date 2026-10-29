"""Read-time derivation of `ready`/`wave`/`referenced_by`/`corrected`.

`ready` and `wave` come from the `depends_on` payload field of `staged`
types, which holds subjects. A subject resolves to the latest record of the
same type (see `RecordIndex.resolve_subject`). A record is ready when every
dependency is in the lifecycle's terminal success state (`done`). A dependency
that is withdrawn, superseded without a successor, or missing is not done.

`wave` is the topological depth of the dependency graph, computed with one
iterative depth-first walk. A cycle makes the wave of every record on it, and
of everything that depends on it, `None`. A dependency that resolves to no
record is skipped for `wave` and blocks `ready`.

`referenced_by` is the inverse of every `relationships` edge (`supersedes`,
`corrects`) and of every resolved `depends_on` edge. A record that another
record corrects also gets `corrected`.

Everything here is read-time only. Callers attach `derived` to a copy of a
record and never hand that copy back to the store.
"""

from __future__ import annotations

from typing import Any, cast

from orchestra.canon.index import RecordIndex
from orchestra.canon.lifecycle import terminal_success_state
from orchestra.canon.schema import DEPENDS_ON, SchemaSet


def eligible_record_types(schemas: SchemaSet) -> set[str]:
    return {name for name, d in schemas.types.items() if DEPENDS_ON in d.fields}


def _dependency_ids(record: dict[str, Any], index: RecordIndex) -> list[str | None]:
    subjects = (record.get("payload") or {}).get(DEPENDS_ON) or []
    ids: list[str | None] = []
    for subject in subjects:
        target = index.resolve_subject(record["record_type"], subject)
        ids.append(target["id"] if target is not None else None)
    return ids


def _is_ready(
    deps: list[str | None],
    by_id: dict[str, dict[str, Any]],
    success_cache: dict[str, str | None],
    schemas: SchemaSet,
) -> bool:
    for dep_id in deps:
        target = by_id.get(dep_id) if dep_id is not None else None
        if target is None:
            return False
        target_type = target["record_type"]
        if target_type not in success_cache:
            type_def = schemas.types.get(target_type)
            success_cache[target_type] = (
                terminal_success_state(type_def.lifecycle) if type_def else None
            )
        success = success_cache[target_type]
        if success is None or target.get("lifecycle_state") != success:
            return False
    return True


def _compute_waves(
    by_id: dict[str, dict[str, Any]], dependencies: dict[str, list[str | None]]
) -> dict[str, int | None]:
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {}
    wave: dict[str, int | None] = {}
    cyclic: set[str] = set()

    def deps_of(record_id: str) -> list[str]:
        return [dep for dep in dependencies.get(record_id, []) if dep is not None]

    for start_id in by_id:
        if color.get(start_id, WHITE) != WHITE:
            continue
        stack: list[list[Any]] = [[start_id, deps_of(start_id), 0]]
        color[start_id] = GRAY
        while stack:
            frame = stack[-1]
            node, deps, idx = frame[0], frame[1], frame[2]
            if idx < len(deps):
                frame[2] += 1
                dep = deps[idx]
                dep_color = color.get(dep, WHITE)
                if dep_color == WHITE:
                    if dep in by_id:
                        color[dep] = GRAY
                        stack.append([dep, deps_of(dep), 0])
                    # else: dangling, no node to descend into
                elif dep_color == GRAY:
                    # back edge: everything on the current path is unresolved
                    for pending_id, _, _ in stack:
                        cyclic.add(pending_id)
                continue
            stack.pop()
            color[node] = BLACK
            if node in cyclic:
                wave[node] = None
                continue
            contributing: list[int] = []
            undefined = False
            for dep in deps:
                if dep not in by_id:
                    continue  # dangling: does not contribute depth
                dep_wave = wave.get(dep)
                if dep_wave is None:
                    undefined = True
                    break
                contributing.append(dep_wave)
            wave[node] = None if undefined else (1 + max(contributing) if contributing else 1)
    return wave


def compute_inverse(records: list[dict[str, Any]]) -> dict[str, dict[str, list[str]]]:
    """{target_id: {relationship_type: [source_id, ...]}} over every relationship
    edge in the record set, regardless of record type.

    Pure data walk: a record's `relationships` dict is always {type: [target_ids]}.
    Source ids are sorted for determinism --
    two records referencing the same target in different id order must not
    make an otherwise-unchanged store's derived output differ.
    """
    inverse: dict[str, dict[str, list[str]]] = {}
    for record in records:
        source_id = cast(str, record.get("id"))
        for rel_type, targets in (record.get("relationships") or {}).items():
            for target_id in targets or []:
                inverse.setdefault(target_id, {}).setdefault(rel_type, []).append(source_id)
    for by_type in inverse.values():
        for sources in by_type.values():
            sources.sort()
    return inverse


def compute_derived(
    records: list[dict[str, Any]], schemas: SchemaSet
) -> dict[str, dict[str, Any]]:
    """{record_id: {...}} of read-time-only values, never persisted.

    Call with the full record set: a dependency can name a record of any
    state, and filtering first would misreport real targets as dangling.
    """
    eligible = eligible_record_types(schemas)
    inverse = compute_inverse(records)
    if not eligible and not inverse:
        return {}
    index = RecordIndex(records)
    by_id = index.by_id
    dependencies = {
        r["id"]: _dependency_ids(r, index) for r in records if r.get("record_type") in eligible
    }
    for source_id, deps in dependencies.items():
        for dep_id in deps:
            if dep_id is not None:
                sources = inverse.setdefault(dep_id, {}).setdefault(DEPENDS_ON, [])
                if source_id not in sources:
                    sources.append(source_id)
    for by_type in inverse.values():
        by_type.get(DEPENDS_ON, []).sort()
    wave = _compute_waves(by_id, dependencies) if eligible else {}
    success_cache: dict[str, str | None] = {}
    derived: dict[str, dict[str, Any]] = {}
    for record in records:
        record_id = record["id"]
        entry: dict[str, Any] = {}
        if record.get("record_type") in eligible:
            entry["ready"] = _is_ready(dependencies[record_id], by_id, success_cache, schemas)
            entry["wave"] = wave.get(record_id)
        if record_id in inverse:
            entry["referenced_by"] = inverse[record_id]
            if "corrects" in inverse[record_id]:
                entry["corrected"] = True
        if entry:
            derived[record_id] = entry
    return derived


def attach_derived(
    record: dict[str, Any], derived_map: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """A copy of `record` with a top-level `derived` mapping, or `record`
    itself, unmodified, when it has no derived values."""
    values = derived_map.get(cast(str, record.get("id")))
    if values is None:
        return record
    out = dict(record)
    out["derived"] = dict(values)
    return out


def attach_derived_all(
    records: list[dict[str, Any]], derived_map: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    if not derived_map:
        return records
    return [attach_derived(record, derived_map) for record in records]
