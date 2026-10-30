"""Pydantic models for every ``/api/*`` response of the dashboard server."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, PlainSerializer, RootModel

Timestamp = Annotated[
    datetime,
    PlainSerializer(lambda value: value.isoformat(), return_type=str, when_used="json"),
]


class Model(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorBody(Model):
    error: str


class OkResponse(Model):
    ok: bool


class TokenResponse(Model):
    token: str


class TaskRow(Model):
    id: str
    subject: str
    title: str
    phase: str
    assignee: str
    wave: int | None
    status: str
    waits_on: list[str]
    depends_on: list[str]
    running_since: Timestamp | None
    size: str
    estimate_minutes: int | None
    executor: str
    last_record_at: Timestamp | None
    attempts: int
    retry_budget: int


class MilestoneRow(Model):
    subject: str
    title: str
    ordinal: int
    state: str
    done: int
    total: int
    id: str


class PhaseSummary(Model):
    subject: str
    title: str
    ordinal: int
    state: str
    done: int
    total: int
    id: str
    awaiting_signoff: bool
    sitting: str
    elapsed_minutes: int | None
    unset_estimates: int
    suite: str
    milestone: str
    milestone_title: str
    stage: str
    verified: int | None
    requirements: int | None
    release_ready: bool


class NeedsYouSummary(Model):
    kind: str
    id: str
    subject: str
    text: str
    record_type: str
    task_id: str
    phase: str
    requirement: str
    status: str
    next: str
    result: str
    revision: str


class BacklogSummary(Model):
    id: str
    subject: str
    text: str
    source: str
    phase: str
    status: str


class EffortSummary(Model):
    effort: str
    goal: str
    position: str
    kind: str
    finished: bool
    release_ready: bool
    phases: list[PhaseSummary]
    milestones: list[MilestoneRow]
    tasks: list[TaskRow]
    needs_you: list[NeedsYouSummary]
    backlog: list[BacklogSummary]


class AreaIdea(Model):
    subject: str
    text: str
    status: str
    area: str
    effort: str
    phase: str


class AreaView(Model):
    subject: str
    title: str
    scope: str
    open_count: int
    ideas: list[AreaIdea]


class AreasResponse(RootModel[list[AreaView]]):
    pass


class SnapshotResponse(Model):
    token: str
    generated_at: str
    store: str
    efforts: list[EffortSummary]


class LinkedTask(Model):
    id: str
    subject: str
    title: str
    status: str


class CheckRun(Model):
    id: str
    result: str
    method: str
    signed_by: str
    revision: str
    recorded_at: Timestamp
    evidence_kind: str


class AcceptanceRow(Model):
    id: str
    subject: str
    criterion: str
    method: str
    verify_command: str
    check: CheckRun | None


class TimelineEvent(Model):
    kind: str
    id: str
    recorded_at: Timestamp
    summary: str
    body: str
    revision: str


class RelatedRecord(Model):
    kind: str
    id: str
    subject: str
    text: str


class AgentAssignment(Model):
    id: str
    subject: str
    recorded_at: Timestamp
    executor: str
    orientation: str
    body: str


class AgentAmendment(Model):
    id: str
    recorded_at: Timestamp
    correction: str


class AgentReport(Model):
    id: str
    recorded_at: Timestamp
    result: str
    verdict: str
    body: str


class AgentWork(Model):
    assignment: AgentAssignment
    amendments: list[AgentAmendment]
    report: AgentReport | None


class TaskDetail(Model):
    id: str
    subject: str
    effort: str
    title: str
    status: str
    phase: str
    wave: int | None
    assignee: str
    body: str
    depends_on: list[LinkedTask]
    blocks: list[LinkedTask]
    acceptances: list[AcceptanceRow]
    timeline: list[TimelineEvent]
    related: list[RelatedRecord]
    running_since: Timestamp | None
    requirements: list[str]
    decisions: list[str]
    size: str
    estimate_minutes: int | None
    executor: str
    agent_work: list[AgentWork]


class TaskResponse(Model):
    detail: TaskDetail


class DecisionChoice(Model):
    subject: str
    choice: str


class IntegrationView(Model):
    result: str
    conflicts: str


class RequirementRow(Model):
    phase: str
    id: str
    text: str
    status: str
    next: str
    latest_check: CheckRun | None
    tasks: int
    tasks_done: int
    confidence: str
    check_kind: str
    check_at: Timestamp | None


class PhaseEvidence(Model):
    phase: str
    weight: str
    requirements: list[RequirementRow]
    stage: str
    integration: IntegrationView | None
    release_ready: bool
    decisions: list[DecisionChoice]
    non_goals: str
    release_state: str


class ProofView(Model):
    id: str
    kind: str
    revision: str
    base: str
    look: str
    attention: str
    machine: str
    diff: str


class PhaseDetail(Model):
    subject: str
    effort: str
    title: str
    state: str
    awaiting_signoff: bool
    body: str
    decisions: list[RelatedRecord]
    constraints: list[RelatedRecord]
    tasks: list[TaskRow]
    evidence: PhaseEvidence | None
    spec_body: str
    design_body: str
    structured: bool
    milestone: str
    milestone_title: str
    proof: ProofView | None


class DecisionEntry(Model):
    subject: str
    phase: str
    choice: str
    alternatives: str
    rationale: str
    counter: str
    superseded: list[DecisionEntry]


class DecisionLog(Model):
    groups: list[tuple[str, list[DecisionEntry]]]


class PhaseResponse(Model):
    detail: PhaseDetail
    tabs: list[str]
    decisions: DecisionLog


class AssessmentView(Model):
    id: str
    status: str
    level: str
    next: str
    confidence: str


class RequirementDetail(Model):
    phase: str
    id: str
    text: str
    status: str
    next: str
    decisions: list[DecisionChoice]
    tasks: list[TaskRow]
    acceptances: list[AcceptanceRow]
    assessments: list[AssessmentView]


class RequirementResponse(Model):
    detail: RequirementDetail


class JournalItem(Model):
    id: str
    record_type: str
    subject: str
    phase: str | None
    recorded_at: Timestamp
    text: str
    open: bool
    task_id: str


class JournalResponse(Model):
    open: list[JournalItem]
    rest: list[JournalItem]


class StoredRecord(Model):
    model_config = ConfigDict(from_attributes=True, extra="allow")

    id: str
    record_type: str
    subject: str
    lifecycle_state: str
    revision: str
    recorded_at: str
    body: str
    payload: dict[str, Any]
    relationships: dict[str, Any]


class RecordResponse(Model):
    record: StoredRecord


class ConfirmChoice(Model):
    action: str
    label: str
    note_required: bool


class Approval(Model):
    confirm_choices: list[ConfirmChoice]


class NeedsYouItem(Model):
    kind: str
    id: str
    subject: str
    text: str
    record_type: str
    body: str
    task_id: str
    phase: str
    requirement: str
    status: str
    next: str
    result: str
    revision: str
    approval: Approval


class NeedsResponse(Model):
    item: NeedsYouItem


class BacklogItem(Model):
    id: str
    subject: str
    effort: str
    text: str
    status: str
    source: str
    phase: str
    body: str
    record_type: str


class BacklogResponse(Model):
    item: BacklogItem
