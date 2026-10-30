"""Read and write surface for the web dashboard FastAPI app."""

from __future__ import annotations

import threading
from dataclasses import replace
from typing import Any, Callable

from dashboard.backend import approval, areas, backlog, dismiss, journal, store
from dashboard.backend.phase import (
    PhaseRow, load_decision_log, load_phase_detail, load_requirement_detail, tabs_for,
)
from dashboard.backend.server import schemas
from dashboard.backend.snapshot import BacklogItem, EffortView, NeedsYouItem, Snapshot, load_snapshot
from dashboard.backend.task import load_task_detail
from orchestra.canon.project import Project


def phase_summary(phase: PhaseRow) -> schemas.PhaseSummary:
    evidence = phase.evidence
    verified = None
    requirements = None
    stage = ""
    release_ready = False
    if evidence is not None:
        requirements = len(evidence.requirements)
        verified = sum(row.status == "verified" for row in evidence.requirements)
        stage = evidence.stage
        release_ready = evidence.release_ready
    return schemas.PhaseSummary(
        subject=phase.subject,
        title=phase.title,
        ordinal=phase.ordinal,
        state=phase.state,
        done=phase.done,
        total=phase.total,
        id=phase.id,
        awaiting_signoff=phase.awaiting_signoff,
        sitting=phase.sitting,
        elapsed_minutes=phase.elapsed_minutes,
        unset_estimates=phase.unset_estimates,
        suite=phase.suite,
        milestone=phase.milestone,
        milestone_title=phase.milestone_title,
        stage=stage,
        verified=verified,
        requirements=requirements,
        release_ready=release_ready,
    )


def effort_summary(view: EffortView) -> schemas.EffortSummary:
    return schemas.EffortSummary(
        effort=view.effort,
        goal=view.goal,
        position=view.position,
        kind=view.kind,
        finished=view.finished,
        release_ready=view.release_ready,
        phases=[phase_summary(phase) for phase in view.phases],
        milestones=[schemas.MilestoneRow.model_validate(row) for row in view.milestones],
        tasks=[schemas.TaskRow.model_validate(row) for row in view.tasks],
        needs_you=[schemas.NeedsYouSummary.model_validate(item) for item in view.needs_you],
        backlog=[schemas.BacklogSummary.model_validate(item) for item in view.backlog],
    )


def needs_payload(item: NeedsYouItem) -> schemas.NeedsYouItem:
    choices = [schemas.ConfirmChoice.model_validate(choice) for choice in approval.confirm_choices(item)]
    return schemas.NeedsYouItem.model_validate(
        {**vars(item), "approval": schemas.Approval(confirm_choices=choices)}
    )


class Cache:
    """Snapshot and detail cache keyed by ``dashboard.backend.store.change_token``."""

    def __init__(self, target: Project) -> None:
        self.target = target
        self.lock = threading.Lock()
        self.token = ""
        self.snapshot: Snapshot | None = None
        self.details: dict[tuple, object] = {}

    def _current(self) -> Snapshot:
        token = store.change_token(self.target)
        with self.lock:
            if self.snapshot is not None and token == self.token:
                return self.snapshot
        snapshot = load_snapshot(self.target, token=token)
        with self.lock:
            if token != self.token:
                self.details.clear()
            self.token = snapshot.token or token
            self.snapshot = snapshot
            return snapshot

    def token_only(self) -> str:
        token = store.change_token(self.target)
        with self.lock:
            if token != self.token:
                self.snapshot = None
                self.details.clear()
                self.token = token
            return self.token

    def drop(self) -> None:
        """Clear snapshot and detail cache after a successful write."""
        with self.lock:
            self.snapshot = None
            self.details.clear()
            self.token = ""

    def snapshot_payload(self) -> schemas.SnapshotResponse:
        snapshot = self._current()
        return schemas.SnapshotResponse(
            token=snapshot.token,
            generated_at=snapshot.generated_at.isoformat(),
            store=str(self.target.store_path),
            efforts=[effort_summary(view) for view in snapshot.efforts],
        )

    def effort(self, name: str) -> EffortView:
        snapshot = self._current()
        for view in snapshot.efforts:
            if view.effort == name:
                return view
        raise store.ModelError(f"effort {name} not found")

    def remember(self, key: tuple, load: Callable[[], Any]) -> Any:
        token = self.token_only()
        with self.lock:
            cached = self.details.get((token, key))
        if cached is not None:
            return cached
        value = load()
        with self.lock:
            if self.token == token:
                self.details[(token, key)] = value
        return value


class Reader:
    """Read accessors and writes behind the FastAPI routes."""

    def __init__(self, target: Project) -> None:
        self.target = target
        self.cache = Cache(target)

    def token(self) -> schemas.TokenResponse:
        return schemas.TokenResponse(token=self.cache.token_only())

    def snapshot(self) -> schemas.SnapshotResponse:
        return self.cache.snapshot_payload()

    def areas(self) -> schemas.AreasResponse:
        return self.cache.remember(
            ("areas",),
            lambda: schemas.AreasResponse([schemas.AreaView.model_validate(view) for view in areas.load_areas(self.target)]),
        )

    def phase(self, effort: str, phase: str) -> schemas.PhaseResponse:
        def load() -> schemas.PhaseResponse:
            detail = load_phase_detail(self.target, effort, phase)
            log = load_decision_log(self.target, effort, phase, history=False)
            return schemas.PhaseResponse(
                detail=schemas.PhaseDetail.model_validate(detail),
                tabs=list(tabs_for(detail)),
                decisions=schemas.DecisionLog.model_validate(log),
            )

        return self.cache.remember(("phase", effort, phase), load)

    def task(self, task_id: str) -> schemas.TaskResponse:
        return self.cache.remember(
            ("task", task_id),
            lambda: schemas.TaskResponse(detail=schemas.TaskDetail.model_validate(load_task_detail(self.target, task_id))),
        )

    def journal(self, effort: str) -> schemas.JournalResponse:
        def load() -> schemas.JournalResponse:
            opened, rest = journal.ordered(journal.load_journal(self.target, effort))
            return schemas.JournalResponse(
                open=[schemas.JournalItem.model_validate(item) for item in opened],
                rest=[schemas.JournalItem.model_validate(item) for item in rest],
            )

        return self.cache.remember(("journal", effort), load)

    def record(self, record_id: str) -> schemas.RecordResponse:
        return self.cache.remember(
            ("record", record_id),
            lambda: schemas.RecordResponse(record=schemas.StoredRecord.model_validate(journal.load_record(self.target, record_id))),
        )

    def requirement(self, effort: str, phase: str, requirement: str) -> schemas.RequirementResponse:
        return self.cache.remember(
            ("requirement", effort, phase, requirement),
            lambda: schemas.RequirementResponse(
                detail=schemas.RequirementDetail.model_validate(
                    load_requirement_detail(self.target, effort, phase, requirement)
                )
            ),
        )

    def needs(self, effort: str, item_id: str) -> schemas.NeedsResponse:
        view = self.cache.effort(effort)
        for item in view.needs_you:
            if item.id == item_id:
                return schemas.NeedsResponse(item=needs_payload(item))
        raise store.ModelError(f"needs-you item {item_id} not found")

    def backlog(self, effort: str, item_id: str) -> schemas.BacklogResponse:
        view = self.cache.effort(effort)
        for item in view.backlog:
            if item.id == item_id:
                return schemas.BacklogResponse(item=schemas.BacklogItem.model_validate(item))
        raise store.ModelError(f"backlog item {item_id} not found")

    def _find_needs(self, item_id: str, effort: str | None = None) -> NeedsYouItem:
        if effort:
            view = self.cache.effort(effort)
            for item in view.needs_you:
                if item.id == item_id:
                    return item
            raise store.ModelError(f"needs-you item {item_id} not found")
        for view in self.cache._current().efforts:
            for item in view.needs_you:
                if item.id == item_id:
                    return item
        raise store.ModelError(f"needs-you item {item_id} not found")

    def _find_backlog(self, item_id: str, effort: str | None = None) -> BacklogItem:
        if effort:
            view = self.cache.effort(effort)
            for item in view.backlog:
                if item.id == item_id:
                    return item
            raise store.ModelError(f"backlog item {item_id} not found")
        for view in self.cache._current().efforts:
            for item in view.backlog:
                if item.id == item_id:
                    return item
        raise store.ModelError(f"backlog item {item_id} not found")

    def write_needs(self, body: dict) -> schemas.OkResponse:
        """POST /api/needs — clear a human Needs-you item through dismiss."""
        item_id = str(body.get("id") or "").strip()
        action = str(body.get("action") or "").strip().lower()
        if not item_id or not action:
            raise WriteError("missing id or action", 400)
        effort = str(body.get("effort") or "").strip() or None
        note_raw = body.get("note")
        note = None if note_raw is None else str(note_raw).strip() or None
        if approval.note_required_for(action) and not note:
            raise WriteError("note required", 400)
        item = self._find_needs(item_id, effort)
        if not dismiss.is_dismissible(item.kind):
            raise WriteError(f"cannot dismiss {item.kind}", 400)
        revision = body.get("revision")
        if revision is not None:
            item = replace(item, revision=str(revision))
        try:
            # Always the process default; ignore any signer field on the body.
            dismiss.dismiss_item(
                self.target,
                item,
                action=action,
                note=note,
                signer=dismiss.default_signer(),
            )
        except dismiss.DismissRefused as exc:
            raise WriteError(str(exc), 400) from exc
        except dismiss.DismissError as exc:
            message = str(exc)
            if message == dismiss.STALE_MESSAGE or "changed since opened" in message.lower():
                raise WriteError(message, 409) from exc
            raise WriteError(message, 400) from exc
        self.cache.drop()
        return schemas.OkResponse(ok=True)

    def write_backlog(self, body: dict) -> schemas.OkResponse:
        """POST /api/backlog — dismiss or promote an open backlog item."""
        item_id = str(body.get("id") or "").strip()
        action = str(body.get("action") or "").strip().lower()
        if not item_id or not action:
            raise WriteError("missing id or action", 400)
        effort = str(body.get("effort") or "").strip() or None
        item = self._find_backlog(item_id, effort)
        try:
            if action == "dismiss":
                backlog.dismiss_item(self.target, item)
            elif action == "promote":
                backlog.promote_item(self.target, item)
            else:
                raise WriteError(f"unsupported action {action!r}", 400)
        except backlog.BacklogRefused as exc:
            raise WriteError(str(exc), 400) from exc
        except backlog.BacklogError as exc:
            raise WriteError(str(exc), 400) from exc
        self.cache.drop()
        return schemas.OkResponse(ok=True)


class WriteError(Exception):
    """HTTP-mapped failure for a Needs-you or backlog write."""

    def __init__(self, message: str, status: int) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
