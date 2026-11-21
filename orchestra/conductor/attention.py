from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from orchestra.canon.types import Record
from orchestra.conductor.model_types import planning_payload as record_payload
from orchestra.conductor.requirements import is_verified, requirement_status
from orchestra.score.lookups import current_phases, latest_record, record_order
from orchestra.score.phase import read_phase
from orchestra.score.workflow_blockers import human_gates

ATTENTION_ORDER = (
    "blocking-question",
    "loop-route",
    "integration",
    "merge-branch",
    "needs-human",
    "unsigned-check",
    "open-question",
)
_UPSTREAM_NEXT = frozenset({"specify", "design", "plan"})
_INACTIVE_STATES = ("superseded", "retracted")
_LIVE_PHASE_STATES = ("planned", "in_progress", "done")


@dataclass(frozen=True)
class LandingFact:
    exists: bool
    merged: bool
    branch: str
    ahead: int


@dataclass(frozen=True)
class AttentionItem:
    kind: str
    record_id: str
    subject: str
    text: str
    phase: str = ""
    requirement: str = ""
    status: str = ""
    next: str = ""
    result: str = ""
    body: str = ""
    record_type: str = ""
    revision: str = ""
    updated_at: datetime | None = None


def _recorded_at(record: Record) -> datetime:
    return datetime.fromisoformat(record["recorded_at"].replace("Z", "+00:00"))


def _live(records: list[Record]) -> list[Record]:
    return [record for record in records if record.get("lifecycle_state") not in _INACTIVE_STATES]


def _effort_of(record: Record) -> str:
    return record_payload(record).get("effort") or ""


def _needs_route(record: Record) -> bool:
    payload = record_payload(record)
    status, nxt, confidence = (
        payload.get("status", ""),
        payload.get("next", ""),
        payload.get("confidence", ""),
    )
    if status == "insufficient" or nxt == "execute":
        return False
    if nxt == "verify" and status != "blocked":
        return False
    return nxt in _UPSTREAM_NEXT or status == "blocked" or confidence == "low"


def _latest_assessments(records: list[Record]) -> dict[tuple[str, str], Record]:
    grouped: dict[tuple[str, str], Record] = {}
    for record in sorted(_live(records), key=record_order):
        payload = record_payload(record)
        grouped[(payload.get("phase", ""), payload.get("requirement", ""))] = record
    return grouped


def _spec_phases(records: list[Record], effort: str) -> set[str]:
    found = {
        record_payload(record).get("phase") or ""
        for record in _live([r for r in records if r["record_type"] == "score:specification"])
        if _effort_of(record) == effort
    }
    for record in current_phases(records).values():
        phase = read_phase(record)
        if phase.effort == effort and phase.weight == "light":
            found.add(phase.subject)
    found.discard("")
    return found


def _gate_items(records: list[Record], effort: str) -> list[AttentionItem]:
    acceptances = {r["id"]: r for r in records if r["record_type"] == "score:acceptance"}
    items: list[AttentionItem] = []
    for gate in human_gates(records):
        record = gate.record
        payload = record_payload(record)
        owner = record["subject"] if gate.kind.endswith("question") else _effort_of(record)
        if owner != effort:
            continue
        if gate.kind == "unsigned-check":
            acceptance = acceptances.get(payload.get("criterion_id", ""))
            subject = acceptance["subject"] if acceptance else record["subject"]
            criterion = record_payload(acceptance).get("criterion", "") if acceptance else ""
            text = f"{criterion} {payload.get('result', '')}".strip()
        elif gate.kind == "needs-human":
            subject, text = record["subject"], payload.get("claim", "")
        else:
            subject, text = record["subject"], payload.get("scope", "")
        items.append(
            AttentionItem(
                gate.kind,
                record["id"],
                subject,
                text,
                body=record.get("body") or "",
                record_type=record.get("record_type", ""),
                revision=record.get("revision") or "",
                updated_at=_recorded_at(record),
            )
        )
    return items


def _route_items(records: list[Record], effort: str) -> list[AttentionItem]:
    spec_phases = _spec_phases(records, effort)
    assessments = [
        r for r in records if r["record_type"] == "conductor:assessment" and _effort_of(r) == effort
    ]
    items: list[AttentionItem] = []
    for (phase, requirement), record in sorted(_latest_assessments(assessments).items()):
        if phase not in spec_phases or not _needs_route(record):
            continue
        payload = record_payload(record)
        derived = requirement_status(records, phase).get(requirement)
        status = derived.status if derived is not None else payload.get("status", "")
        if is_verified(status):
            continue
        nxt = payload.get("next", "")
        items.append(
            AttentionItem(
                "loop-route",
                record["id"],
                record["subject"],
                " ".join(part for part in (requirement, status, nxt) if part),
                phase=phase,
                requirement=requirement,
                status=status,
                next=nxt,
                record_type=record.get("record_type", ""),
                revision=record.get("revision") or "",
                updated_at=_recorded_at(record),
            )
        )
    return items


def _integration_items(records: list[Record], effort: str) -> list[AttentionItem]:
    spec_phases = _spec_phases(records, effort)
    by_phase: dict[str, list[Record]] = {}
    for record in _live(
        [
            r
            for r in records
            if r["record_type"] == "conductor:integration-report" and _effort_of(r) == effort
        ]
    ):
        phase = record_payload(record).get("phase", "")
        if phase in spec_phases:
            by_phase.setdefault(phase, []).append(record)
    items: list[AttentionItem] = []
    for phase, reports in by_phase.items():
        latest = latest_record(reports)
        if latest is None:
            continue
        result = record_payload(latest).get("result", "")
        if result not in ("fail", "blocked"):
            continue
        items.append(
            AttentionItem(
                "integration",
                latest["id"],
                latest["subject"],
                f"{phase} {result}",
                phase=phase,
                result=result,
                record_type=latest.get("record_type", ""),
                revision=latest.get("revision") or "",
                updated_at=_recorded_at(latest),
            )
        )
    return items


def _merge_items(
    records: list[Record], effort: str, landing: Mapping[str, LandingFact]
) -> list[AttentionItem]:
    phases = [
        read_phase(record)
        for record in current_phases(records).values()
        if record["lifecycle_state"] in _LIVE_PHASE_STATES
    ]
    items: list[AttentionItem] = []
    for phase in sorted(phases, key=lambda row: row.ordinal):
        if phase.effort != effort or phase.record["lifecycle_state"] != "done":
            continue
        state = landing.get(phase.subject)
        if state is None or not state.exists or state.merged:
            continue
        items.append(
            AttentionItem(
                "merge-branch",
                f"merge:{phase.subject}",
                phase.subject,
                state.branch,
                phase=phase.subject,
                body=f"{state.ahead} ahead",
            )
        )
    return items


def attention_items(
    records: list[Record], effort: str, landing: Mapping[str, LandingFact]
) -> list[AttentionItem]:
    items = [
        *_gate_items(records, effort),
        *_route_items(records, effort),
        *_integration_items(records, effort),
        *_merge_items(records, effort, landing),
    ]
    items.sort(key=lambda entry: ATTENTION_ORDER.index(entry.kind))
    return items
