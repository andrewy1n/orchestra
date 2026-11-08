from __future__ import annotations

from collections.abc import Sequence

from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.score.analyze import analyze_phase
from orchestra.score.workflow_reviews import (
    Authority,
    Step,
    WorkflowReviewError,
    has_blocking_behavior_question,
    step_input_fingerprint,
)


def _latest_review(records: Sequence[Record], phase: str, step: Step) -> Record | None:
    reviews = [
        record
        for record in records
        if record["record_type"] == "score:step-review"
        and record["payload"].get("phase") == phase
        and record["payload"].get("step") == step
    ]
    return (
        max(reviews, key=lambda record: (record["recorded_at"], record["id"])) if reviews else None
    )


def _required_source_reviews(records: Sequence[Record], phase: str, step: Step) -> list[Record]:
    dependencies: tuple[Step, ...]
    if step == "design":
        dependencies = ("spec",)
    elif step == "tasks":
        dependencies = ("spec", "design")
    else:
        dependencies = ()
    reviews = [_latest_review(records, phase, dependency) for dependency in dependencies]
    if any(review is None for review in reviews):
        raise WorkflowReviewError(f"{step} review requires current upstream reviews")
    return [review for review in reviews if review is not None]


def _analysis_errors(records: Sequence[Record], phase: str, step: Step) -> list[str]:
    if step not in ("spec", "design"):
        return []
    report = analyze_phase(records, phase, stage=step)
    return [finding.message for finding in report.findings if finding.severity == "error"]


def _check_authority(
    project: Project, phase_record: Record, step: Step, authority: Authority
) -> None:
    if step != "tasks" and authority == "task-plan-policy":
        raise WorkflowReviewError("task-plan policy can only approve task planning")
    if authority == "task-plan-policy":
        effort_subject = phase_record["payload"].get("effort")
        if not isinstance(effort_subject, str):
            raise WorkflowReviewError("phase has no effort")
        effort = project.resolve("score:effort", effort_subject)
        if effort["payload"].get("autonomy") not in ("auto-plan", "auto-phases"):
            raise WorkflowReviewError("task-plan policy does not permit this review")


def record_step_review(
    project: Project,
    *,
    phase: str,
    step: Step,
    artifact: Record,
    authority: Authority | None,
    basis: str | None,
    source_reviews: Sequence[Record] = (),
) -> Record:
    token = project.change_token()
    records = project.records()
    phases = [
        record
        for record in records
        if record["record_type"] == "score:phase" and record["subject"] == phase
    ]
    if not phases:
        raise WorkflowReviewError(f"unknown phase {phase!r}")
    phase_record = max(phases, key=lambda record: (record["recorded_at"], record["id"]))
    if step == "spec" and has_blocking_behavior_question(records, phase):
        raise WorkflowReviewError("blocking behavior question prevents specification readiness")
    current_artifact = next((record for record in records if record["id"] == artifact["id"]), None)
    if current_artifact is None or current_artifact["revision"] != artifact["revision"]:
        raise WorkflowReviewError("reviewed artifact changed before review")
    required_sources = _required_source_reviews(records, phase, step)
    sources = list(source_reviews) if source_reviews else required_sources
    if [record["id"] for record in sources] != [record["id"] for record in required_sources]:
        raise WorkflowReviewError("review sources are not current")
    if step in ("spec", "design"):
        errors = _analysis_errors(records, phase, step)
        if errors:
            raise WorkflowReviewError("; ".join(errors))
    fingerprint = step_input_fingerprint(step, current_artifact, sources, records)
    existing = _latest_review(records, phase, step)
    if existing is not None and (
        existing["payload"].get("reviewed_artifact") == current_artifact["id"]
        and existing["payload"].get("input_fingerprint") == fingerprint
        and existing["payload"].get("source_reviews") == [record["id"] for record in sources]
    ):
        return existing
    if authority is None or not basis:
        raise WorkflowReviewError("a new review requires an authority and basis")
    _check_authority(project, phase_record, step, authority)
    effort = phase_record["payload"].get("effort")
    if not isinstance(effort, str):
        raise WorkflowReviewError("phase has no effort")
    subject = f"{phase}-{step}-{fingerprint[:16]}"
    project.apply_at_snapshot(
        [
            {
                "op": "create",
                "type": "score:step-review",
                "subject": subject,
                "payload": {
                    "effort": effort,
                    "phase": phase,
                    "step": step,
                    "reviewed_artifact": current_artifact["id"],
                    "reviewed_revision": current_artifact["revision"],
                    "input_fingerprint": fingerprint,
                    "source_reviews": [record["id"] for record in sources],
                    "authority": authority,
                    "basis": basis,
                },
            }
        ],
        token,
    )
    return project.resolve("score:step-review", subject)
