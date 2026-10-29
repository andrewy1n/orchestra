"""Journal model: load, scope, open-first order."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from orchestra.canon.project import Project
from dashboard.backend import model, store

JOURNAL_TYPES = (
    "conductor:failed-attempt",
    "tuner:investigation-observation",
    "tuner:finding",
    "score:continuity-question",
    "conductor:assignment-amendment",
)
PLAN_REVIEW_PREFIX = "plan-review:"
FINDING_OPEN_STATES = ("asserted", "supported", "disputed")
KIND_JOURNAL = frozenset({"repair", "evaluate"})
SEPARATOR_KEY = "__separator__"
TYPE_LABEL = {
    "conductor:failed-attempt": ("✗", "attempt"),
    "tuner:investigation-observation": ("◉", "observation"),
    "tuner:finding": ("!", "finding"),
    "score:continuity-question": ("?", "question"),
    "conductor:assignment-amendment": ("△", "amendment"),
}


@dataclass(frozen=True)
class JournalItem:
    id: str
    record_type: str
    subject: str
    phase: str | None
    recorded_at: datetime
    text: str
    open: bool
    task_id: str = ""


def _soft_list(target: Project, record_type: str, *, payload: dict[str, str] | None = None) -> list[dict[str, Any]]:
    try:
        return model._list(target, record_type, payload=payload)
    except model.ModelError:
        return []


def _phase_for_task(subject: str, tasks: list[dict[str, Any]]) -> tuple[str | None, str]:
    matches = [
        task for task in tasks
        if subject == task["subject"] or subject.startswith(task["subject"] + "-")
    ]
    if not matches:
        return None, ""
    task = max(matches, key=lambda item: len(item["subject"]))
    return model._payload(task).get("phase") or None, task["id"]


def _plan_review_slug(scope: str) -> str | None:
    if not scope.startswith(PLAN_REVIEW_PREFIX):
        return None
    return scope[len(PLAN_REVIEW_PREFIX):]


def _question_scope_text(scope: str, phase_titles: dict[str, str]) -> str:
    slug = _plan_review_slug(scope)
    if slug is not None:
        return phase_titles.get(slug, slug)
    return scope


def _question_open(record: dict[str, Any]) -> bool:
    return record.get("lifecycle_state") == "open"


def _finding_open(record: dict[str, Any]) -> bool:
    return (
        model._payload(record).get("needs") == "human"
        and record.get("lifecycle_state") in FINDING_OPEN_STATES
    )


def _first_line(text: str) -> str:
    for line in (text or "").splitlines():
        if line.strip():
            return line.strip()
    return ""


def _attempt_text(payload: dict[str, Any]) -> str:
    parts = [payload.get("attempted_action") or "", "don't retry"]
    retry = payload.get("retry_when") or ""
    if retry:
        parts.append(f"retry when {retry}")
    return " · ".join(part for part in parts if part)


def _finding_text(payload: dict[str, Any]) -> str:
    claim = payload.get("claim") or ""
    needs = payload.get("needs") or ""
    if claim and needs:
        return f"{claim} · needs {needs}"
    return claim or needs


def _question_text(record: dict[str, Any], phase_titles: dict[str, str]) -> str:
    scope = model._payload(record).get("scope") or ""
    shown = _question_scope_text(scope, phase_titles)
    state = record.get("lifecycle_state") or ""
    if shown and state:
        return f"{shown} · {state}"
    return shown or state


def _amendment_text(record: dict[str, Any], task_subject: str) -> str:
    correction = _first_line(model._section(record.get("body") or "", "Correction"))
    if correction and task_subject:
        return f"{correction} · {task_subject}"
    return correction or task_subject


def _belongs_to_effort(
    record: dict[str, Any], effort: str, *, sole_goal: bool, by_subject: bool = False,
) -> bool:
    if by_subject:
        return record.get("subject") == effort
    payload_effort = model._payload(record).get("effort")
    if payload_effort:
        return payload_effort == effort
    return sole_goal


def _assignment_task(
    record: dict[str, Any],
    assignments: dict[str, dict[str, Any]],
    tasks_by_id: dict[str, dict[str, Any]],
    tasks_by_subject: dict[str, dict[str, Any]],
) -> tuple[str | None, str, str]:
    ref = model._payload(record).get("assignment") or ""
    assignment = assignments.get(ref)
    if assignment is None:
        phase, task_id = _phase_for_task(record["subject"], list(tasks_by_subject.values()))
        return phase, task_id, record["subject"] if task_id else ""
    work_ref = model._payload(assignment).get("work_item") or ""
    task = tasks_by_id.get(work_ref) or tasks_by_subject.get(work_ref)
    if task is None:
        phase, task_id = _phase_for_task(assignment["subject"], list(tasks_by_subject.values()))
        return phase, task_id, assignment["subject"] if task_id else assignment["subject"]
    return model._payload(task).get("phase") or None, task["id"], task["subject"]


def load_journal(target: Project, effort: str) -> list[JournalItem]:
    """List the five journal types for an effort; missing types become empty (R9)."""
    aliases = model._merge_aliases(model._list(target, "score:effort"))
    goals = [
        record for record in model._list(target, "score:effort")
        if record.get("lifecycle_state") == "active"
        and model._payload(record).get("status") != "closed"
    ]
    sole_goal = len(goals) == 1 and (not goals or goals[0]["subject"] == effort)

    tasks = model._remapped(
        _soft_list(target, "score:work-item", payload={"effort": effort}),
        aliases,
    )
    if not tasks:
        tasks = [
            record for record in model._remapped(_soft_list(target, "score:work-item"), aliases)
            if model._payload(record).get("effort") == effort
        ]
    tasks_by_id = {task["id"]: task for task in tasks}
    tasks_by_subject = {task["subject"]: task for task in tasks}

    phases = model._remapped(
        _soft_list(target, "score:phase", payload={"effort": effort}),
        aliases,
    )
    phase_titles = {
        record["subject"]: model._payload(record).get("title") or record["subject"]
        for record in phases
    }

    assignments_listed = model._remapped(_soft_list(target, "conductor:assignment"), aliases)
    assignments: dict[str, dict[str, Any]] = {}
    for record in assignments_listed:
        assignments[record["id"]] = record
        assignments[record["subject"]] = record

    listed: dict[str, list[dict[str, Any]]] = {}
    for record_type in JOURNAL_TYPES:
        raw = model._remapped(_soft_list(target, record_type), aliases)
        by_subject = record_type == "score:continuity-question"
        listed[record_type] = [
            record for record in raw
            if record.get("lifecycle_state") not in model.INACTIVE_STATES
            and _belongs_to_effort(record, effort, sole_goal=sole_goal, by_subject=by_subject)
        ]

    finding_subjects = {record["subject"] for record in listed["tuner:finding"]}
    items: list[JournalItem] = []

    for record in listed["conductor:failed-attempt"]:
        phase, task_id = _phase_for_task(record["subject"], tasks)
        items.append(JournalItem(
            record["id"], record["record_type"], record["subject"], phase,
            model._recorded_at(record), _attempt_text(model._payload(record)), False, task_id,
        ))

    for record in listed["tuner:investigation-observation"]:
        phase, task_id = _phase_for_task(record["subject"], tasks)
        open_item = record["subject"] not in finding_subjects
        items.append(JournalItem(
            record["id"], record["record_type"], record["subject"], phase,
            model._recorded_at(record),
            model._payload(record).get("what_was_observed") or "",
            open_item, task_id,
        ))

    for record in listed["tuner:finding"]:
        phase, task_id = _phase_for_task(record["subject"], tasks)
        items.append(JournalItem(
            record["id"], record["record_type"], record["subject"], phase,
            model._recorded_at(record), _finding_text(model._payload(record)),
            _finding_open(record), task_id,
        ))

    for record in listed["score:continuity-question"]:
        scope = model._payload(record).get("scope") or ""
        slug = _plan_review_slug(scope)
        phase = slug if slug is not None else None
        items.append(JournalItem(
            record["id"], record["record_type"], record["subject"], phase,
            model._recorded_at(record), _question_text(record, phase_titles),
            _question_open(record), "",
        ))

    for record in listed["conductor:assignment-amendment"]:
        phase, task_id, task_subject = _assignment_task(
            record, assignments, tasks_by_id, tasks_by_subject,
        )
        items.append(JournalItem(
            record["id"], record["record_type"], record["subject"], phase,
            model._recorded_at(record), _amendment_text(record, task_subject),
            False, task_id,
        ))

    return items


def journal_scope(items: list[JournalItem], phase: str | None) -> list[JournalItem]:
    """Phase items plus effort-only open questions; None returns every item (R2)."""
    if phase is None:
        return list(items)
    scoped: list[JournalItem] = []
    for item in items:
        if item.phase == phase:
            scoped.append(item)
        elif item.phase is None and item.open and item.record_type == "score:continuity-question":
            scoped.append(item)
    return scoped


def ordered(items: list[JournalItem]) -> tuple[list[JournalItem], list[JournalItem]]:
    """Open items newest first, then every other item newest first (R4)."""
    open_items = sorted((item for item in items if item.open), key=lambda item: item.recorded_at, reverse=True)
    rest = sorted((item for item in items if not item.open), key=lambda item: item.recorded_at, reverse=True)
    return open_items, rest


def filter_items(items: list[JournalItem], needle: str) -> list[JournalItem]:
    """Keep items whose subject or text contains *needle* (case-insensitive) (R6)."""
    needle = needle.strip().lower()
    if not needle:
        return list(items)
    return [
        item for item in items
        if needle in item.subject.lower() or needle in item.text.lower()
    ]


def load_record(target: Project, record_id: str) -> dict[str, Any]:
    """Fetch one record by id (type optional on the CLI)."""
    record = store.get_record(target, record_id)
    if "subject" not in record:
        raise model.ModelError(f"get {record_id} returned unreadable output")
    return record


def list_markdown(items: list[JournalItem], *, scope: str) -> str:
    """Markdown for the whole journal list (pager)."""
    open_items, rest = ordered(items)
    lines = [f"# Journal ({scope})", ""]
    if open_items:
        lines.append("## Open")
        lines.append("")
        for item in open_items:
            _, label = TYPE_LABEL.get(item.record_type, ("·", item.record_type))
            lines.append(f"- **{label}** `{item.subject}` — {item.text}")
        lines.append("")
    if rest:
        lines.append("## Rest")
        lines.append("")
        for item in rest:
            _, label = TYPE_LABEL.get(item.record_type, ("·", item.record_type))
            lines.append(f"- **{label}** `{item.subject}` — {item.text}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def record_markdown(record: dict[str, Any]) -> str:
    """Markdown for one record: type, subject, payload, body (R5)."""
    payload = model._payload(record)
    lines = [
        f"# {record.get('record_type', '')}",
        "",
        f"**subject:** `{record.get('subject', '')}`",
        "",
    ]
    if payload:
        lines.append("## Payload")
        lines.append("")
        for key, value in payload.items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")
    body = (record.get("body") or "").strip()
    if body:
        lines.append("## Body")
        lines.append("")
        lines.append(body)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
