from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from orchestra.canon import record_payload
from orchestra.canon.project import Project, open_store
from orchestra.canon.types import Record
from orchestra.conductor.landing import LANDING, PROOF_PACKET, latest_landing, proof_packet
from orchestra.metrics.instants import parse_instant
from orchestra.metrics.ops import belongs_to, count_operations, tasks_of
from orchestra.score.lookups import latest_record
from orchestra.score.phase import Phase, current_phase_model

CHECK_RUN = "tuner:check-run"
REPAIR_LINK = "conductor:repair-link"
QUESTION = "score:continuity-question"
STEP_REVIEW = "score:step-review"
AMENDMENT = "tuner:oracle-amendment"


@dataclass(frozen=True)
class PhaseRow:
    phase: str
    effort: str
    weight: str | None
    tasks: int
    landing_time: str | None
    landing_source: str | None
    elapsed_seconds: float | None
    review_rounds: int = 0
    failed_check_runs: int = 0
    human_decisions: int = 0
    repairs_by_cause: dict[str, int] = field(default_factory=dict)
    operations_per_task: float | None = None
    missing: dict[str, str] = field(default_factory=dict)


def _text(record: Record, key: str) -> str:
    value = record_payload(record).get(key)
    return value if isinstance(value, str) else ""


def _landing(records: list[Record], phase: Phase, members: set[str]) -> tuple[str, str] | None:
    landing = latest_landing(records, phase.subject)
    if landing is not None:
        return landing.recorded_at, LANDING
    packet = proof_packet(records, phase)
    if packet is not None:
        return packet.recorded_at, PROOF_PACKET
    check = latest_record(
        r for r in records if r["record_type"] == CHECK_RUN and r["id"] in members
    )
    if check is not None:
        return check["recorded_at"], CHECK_RUN
    return None


def _human_decisions(records: list[Record], phase: str) -> int:
    total = 0
    for r in records:
        if _text(r, "phase") != phase:
            continue
        kind = r["record_type"]
        if kind == QUESTION:
            total += bool(_text(r, "answer"))
        elif kind == STEP_REVIEW:
            total += _text(r, "authority") == "user-approval"
        elif kind == AMENDMENT:
            total += 1
    return total


def _row(project: Project, records: list[Record], phase_model: Phase) -> PhaseRow:
    phase = phase_model.subject
    weight = phase_model.weight
    acceptance_ids = {
        r["id"]
        for r in records
        if r["record_type"] == "score:acceptance" and _text(r, "phase") == phase
    }
    tasks = tasks_of(records, phase)
    subjects = {t["subject"] for t in tasks}
    members = {r["id"] for r in records if belongs_to(r, phase, acceptance_ids, subjects)}
    missing: dict[str, str] = {}
    if weight is None:
        missing["weight"] = "the phase record has no weight"
    landed = _landing(records, phase_model, members)
    landing_time = landed[0] if landed else None
    landing_source = landed[1] if landed else None
    if landed is None:
        missing["landing_time"] = "no landing record, proof packet or check-run for the phase"
    specs = [
        r["recorded_at"]
        for r in records
        if r["record_type"] == "score:specification" and _text(r, "phase") == phase
    ]
    elapsed: float | None = None
    if not specs:
        missing["elapsed_seconds"] = "the phase has no specification record"
    elif landing_time is None:
        missing["elapsed_seconds"] = "the landing time is missing"
    else:
        elapsed = (parse_instant(landing_time) - parse_instant(min(specs))).total_seconds()
    checks = [r for r in records if r["record_type"] == CHECK_RUN and r["id"] in members]
    review_rounds = sum(1 for r in checks if _text(r, "method") == "review")
    failed_check_runs = sum(1 for r in checks if _text(r, "result") == "fail")
    human_decisions = _human_decisions(records, phase)
    repairs_by_cause = dict(
        Counter(
            _text(r, "cause")
            for r in records
            if r["record_type"] == REPAIR_LINK and _text(r, "phase") == phase
        )
    )
    operations_per_task: float | None = None
    if not tasks:
        missing["operations_per_task"] = "the phase has no tasks"
    else:
        counts, task_count = count_operations(project, phase)
        operations_per_task = sum(counts.values()) / task_count
    return PhaseRow(
        phase=phase,
        effort=phase_model.effort,
        weight=weight,
        tasks=len(tasks),
        landing_time=landing_time,
        landing_source=landing_source,
        elapsed_seconds=elapsed,
        review_rounds=review_rounds,
        failed_check_runs=failed_check_runs,
        human_decisions=human_decisions,
        repairs_by_cause=repairs_by_cause,
        operations_per_task=operations_per_task,
        missing=missing,
    )


def build_phase_rows(directory: Path, *, effort: str | None = None) -> list[PhaseRow]:
    project = open_store(directory, read_only=True)
    records = project.records()
    slugs = dict.fromkeys(r["subject"] for r in records if r["record_type"] == "score:phase")
    current = (current_phase_model(slug, records) for slug in slugs)
    phases = [
        p
        for p in current
        if p is not None
        and p.record["lifecycle_state"] == "done"
        and (effort is None or p.effort == effort)
    ]
    return [_row(project, records, p) for p in phases]
