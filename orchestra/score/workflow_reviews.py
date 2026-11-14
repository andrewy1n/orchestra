from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from orchestra.canon.types import JsonValue, Record

Step = Literal["spec", "design", "tasks", "execute", "verify", "land"]
Authority = Literal["user-approval", "explicit-delegation", "task-plan-policy"]
ReadinessStatus = Literal["ready", "missing", "blocked", "stale"]

_CONTRACT_SECTIONS = ("Problem", "Requirements", "Non-goals", "Invariants", "Assumptions")
_APPROACH_SECTIONS = ("Approach", "Architecture", "Interfaces", "Decisions", "Tradeoffs", "Risks")
_PROOF_SECTIONS = ("Exit criteria", "Proof", "Verification", "Acceptance criteria")


@dataclass(frozen=True)
class LightPhaseFingerprints:
    contract: str
    approach: str
    proof: str


@dataclass(frozen=True)
class StepReadiness:
    step: Step
    status: ReadinessStatus
    review: Record | None
    reason: str | None = None


class WorkflowReviewError(ValueError):
    pass


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sections(body: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line.rstrip())
    return sections


def _section_fingerprint(sections: dict[str, list[str]], names: tuple[str, ...]) -> str:
    content = "\n".join(
        f"## {name}\n" + "\n".join(sections[name]).strip() for name in names if name in sections
    )
    return _fingerprint(content)


def light_phase_fingerprints(body: str) -> LightPhaseFingerprints:
    sections = _sections(body)
    return LightPhaseFingerprints(
        contract=_section_fingerprint(sections, _CONTRACT_SECTIONS),
        approach=_section_fingerprint(sections, _APPROACH_SECTIONS),
        proof=_section_fingerprint(sections, _PROOF_SECTIONS),
    )


def _phase_record(records: Sequence[Record], phase: str) -> Record | None:
    candidates = [
        record
        for record in records
        if record["record_type"] == "score:phase"
        and record["subject"] == phase
        and record["lifecycle_state"] != "superseded"
    ]
    return (
        max(candidates, key=lambda record: (record["recorded_at"], record["id"]))
        if candidates
        else None
    )


def _latest_step_review(records: Sequence[Record], phase: str, step: Step) -> Record | None:
    candidates = [
        record
        for record in records
        if record["record_type"] == "score:step-review"
        and record["payload"].get("phase") == phase
        and record["payload"].get("step") == step
    ]
    artifact = _artifact_for_step(records, phase, step)
    dependencies: tuple[Step, ...]
    if step == "design":
        dependencies = ("spec",)
    elif step == "tasks":
        dependencies = ("spec", "design")
    else:
        dependencies = ()
    sources = [_latest_step_review(records, phase, dependency) for dependency in dependencies]
    if artifact is not None and all(source is not None for source in sources):
        current_sources = [source for source in sources if source is not None]
        source_ids = [source["id"] for source in current_sources]
        fingerprint = step_input_fingerprint(step, artifact, current_sources, records)
        current = [
            record
            for record in candidates
            if record["payload"].get("reviewed_artifact") == artifact["id"]
            and record["payload"].get("source_reviews") == source_ids
            and record["payload"].get("input_fingerprint") == fingerprint
        ]
        if current:
            return max(current, key=lambda record: (record["recorded_at"], record["id"]))
    return (
        max(candidates, key=lambda record: (record["recorded_at"], record["id"]))
        if candidates
        else None
    )


def _active_artifact(records: Sequence[Record], phase: str, record_type: str) -> Record | None:
    candidates = [
        record
        for record in records
        if record["record_type"] == record_type
        and record["payload"].get("phase") == phase
        and record["lifecycle_state"] == "active"
    ]
    return (
        max(candidates, key=lambda record: (record["recorded_at"], record["id"]))
        if candidates
        else None
    )


def _artifact_for_step(records: Sequence[Record], phase: str, step: Step) -> Record | None:
    phase_record = _phase_record(records, phase)
    if phase_record is None:
        return None
    light = phase_record["payload"].get("weight") == "light"
    if light:
        return phase_record
    if step == "spec":
        return _active_artifact(records, phase, "score:specification")
    if step == "design":
        return _active_artifact(records, phase, "score:design")
    if step in ("tasks", "execute", "verify", "land"):
        return phase_record
    return None


def _behavior_question(record: Record, phase: str) -> bool:
    payload = record["payload"]
    if (
        record["record_type"] != "score:continuity-question"
        or record["lifecycle_state"] not in ("open", "deferred")
        or payload.get("phase") != phase
        or payload.get("blocking") is not True
    ):
        return False
    scope = payload.get("scope")
    question = payload.get("question")
    text = " ".join(item for item in (scope, question) if isinstance(item, str)).lower()
    return any(term in text for term in ("spec", "behavior", "behaviour"))


def has_blocking_behavior_question(records: Sequence[Record], phase: str) -> bool:
    return any(_behavior_question(record, phase) for record in records)


def _source_reviews(records: Sequence[Record], phase: str, step: Step) -> list[Record]:
    dependencies: tuple[Step, ...]
    if step == "design":
        dependencies = ("spec",)
    elif step == "tasks":
        dependencies = ("spec", "design")
    else:
        dependencies = ()
    reviews = [_latest_step_review(records, phase, dependency) for dependency in dependencies]
    return [review for review in reviews if review is not None]


def _light_step_fingerprint(step: Step, artifact: Record) -> str:
    fingerprints = light_phase_fingerprints(artifact.get("body", ""))
    if step == "spec":
        parts = (fingerprints.contract,)
    elif step == "design":
        parts = (fingerprints.contract, fingerprints.approach)
    elif step == "tasks":
        parts = (fingerprints.contract, fingerprints.approach, fingerprints.proof)
    else:
        parts = (fingerprints.contract, fingerprints.approach, fingerprints.proof)
    return _fingerprint("\0".join(parts))


def _task_plan_fingerprint(phase: str, records: Sequence[Record]) -> str:
    work_items: list[dict[str, JsonValue]] = []
    for record in records:
        if (
            record["record_type"] != "score:work-item"
            or record["payload"].get("phase") != phase
            or record["lifecycle_state"] == "superseded"
        ):
            continue
        payload = record["payload"]
        item: dict[str, JsonValue] = {"subject": record["subject"]}
        for key in (
            "title",
            "kind",
            "executor",
            "requirements",
            "decisions",
            "depends_on",
            "size",
            "estimate_minutes",
        ):
            if key in payload:
                item[key] = payload[key]
        item["body"] = record.get("body", "")
        work_items.append(item)
    acceptances: list[dict[str, JsonValue]] = []
    for record in records:
        if (
            record["record_type"] != "score:acceptance"
            or record["payload"].get("phase") != phase
            or record["lifecycle_state"] != "active"
        ):
            continue
        payload = record["payload"]
        item = {"subject": record["subject"]}
        for key in ("requirement", "requirements", "method", "verify_command"):
            if key in payload:
                item[key] = payload[key]
        acceptances.append(item)

    def subject_key(item: dict[str, JsonValue]) -> str:
        subject = item.get("subject")
        return subject if isinstance(subject, str) else ""

    return _fingerprint(
        json.dumps(
            {
                "work_items": sorted(work_items, key=subject_key),
                "acceptances": sorted(acceptances, key=subject_key),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def step_input_fingerprint(
    step: Step,
    artifact: Record,
    source_reviews: Sequence[Record],
    records: Sequence[Record] = (),
) -> str:
    if artifact["record_type"] == "score:phase" and artifact["payload"].get("weight") == "light":
        artifact_fingerprint = _light_step_fingerprint(step, artifact)
        if step == "tasks":
            artifact_fingerprint = _fingerprint(
                artifact_fingerprint + _task_plan_fingerprint(artifact["subject"], records)
            )
    elif step == "tasks" and artifact["record_type"] == "score:phase":
        artifact_fingerprint = _task_plan_fingerprint(artifact["subject"], records)
    else:
        artifact_fingerprint = f"{artifact['id']}:{artifact['revision']}"
    sources = [f"{review['id']}:{review['revision']}" for review in source_reviews]
    return _fingerprint(json.dumps([step, artifact_fingerprint, sources], separators=(",", ":")))


def _review_sources(review: Record) -> list[str]:
    values = review["payload"].get("source_reviews", [])
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, str)]


def _review_authority_valid(step: Step, review: Record) -> bool:
    authority = review["payload"].get("authority")
    if step in ("spec", "design"):
        return authority in ("user-approval", "explicit-delegation")
    return authority in ("user-approval", "explicit-delegation", "task-plan-policy")


def step_readiness(records: Sequence[Record], phase: str, step: Step) -> StepReadiness:
    if step == "spec" and has_blocking_behavior_question(records, phase):
        return StepReadiness(
            step, "blocked", _latest_step_review(records, phase, step), "blocking behavior question"
        )
    artifact = _artifact_for_step(records, phase, step)
    if artifact is None:
        return StepReadiness(step, "missing", None, "reviewed output is missing")
    review = _latest_step_review(records, phase, step)
    if review is None:
        return StepReadiness(step, "missing", None, "approval review is missing")
    upstream_steps: tuple[Step, ...]
    if step == "design":
        upstream_steps = ("spec",)
    elif step == "tasks":
        upstream_steps = ("spec", "design")
    else:
        upstream_steps = ()
    for upstream_step in upstream_steps:
        upstream = step_readiness(records, phase, upstream_step)
        if upstream.status != "ready":
            return StepReadiness(
                step, "stale", review, f"{upstream_step} review is {upstream.status}"
            )
    sources = _source_reviews(records, phase, step)
    if len(sources) != len(upstream_steps):
        return StepReadiness(step, "missing", review, "upstream review is missing")
    source_ids = [record["id"] for record in sources]
    if review["payload"].get("reviewed_artifact") != artifact["id"]:
        return StepReadiness(step, "stale", review, "reviewed artifact changed")
    if (
        artifact["record_type"] != "score:phase"
        and review["payload"].get("reviewed_revision") != artifact["revision"]
    ):
        return StepReadiness(step, "stale", review, "reviewed revision changed")
    if _review_sources(review) != source_ids:
        return StepReadiness(step, "stale", review, "source reviews changed")
    if review["payload"].get("input_fingerprint") != step_input_fingerprint(
        step, artifact, sources, records
    ):
        return StepReadiness(step, "stale", review, "reviewed inputs changed")
    if not _review_authority_valid(step, review):
        return StepReadiness(step, "missing", review, "review lacks required authority")
    return StepReadiness(step, "ready", review)
