from __future__ import annotations

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record

LATE = "2099-01-01T00:00:00+00:00"


def supersede_phase(
    project: Project, phase: Record, *, payload: JsonObject, body: str | None = None
) -> tuple[Record, Record]:
    result = project.supersede(phase["id"], payload=payload, body=body)
    return result["record"], result["predecessor"]


def restamp(project: Project, record: Record, *, state: str | None = None) -> Record:
    store, _ = project._session()
    changed = Record(**record)
    changed["recorded_at"] = LATE
    if state is not None:
        changed["lifecycle_state"] = state
    return store.write_record(changed, expected_revision=record["revision"])


def supersede_late(
    project: Project, phase: Record, *, payload: JsonObject, body: str | None = None
) -> tuple[Record, Record]:
    current, stale = supersede_phase(project, phase, payload=payload, body=body)
    return current, restamp(project, stale)


def retire(project: Project, record: Record) -> Record:
    store, _ = project._session()
    changed = Record(**record)
    changed["lifecycle_state"] = "superseded"
    return store.write_record(changed, expected_revision=record["revision"])


def supersede_all(project: Project, phase: Record, *, payload: JsonObject) -> list[Record]:
    current, stale = supersede_phase(project, phase, payload=payload)
    return [retire(project, current), stale]
