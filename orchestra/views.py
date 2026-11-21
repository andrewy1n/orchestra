"""Markdown views rendered from canon records: handoff, plan, status, verification, brief."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from orchestra.canon import record_payload
from orchestra.canon.project import Project
from orchestra.canon.project_config import load_project_config
from orchestra.canon.sections import body_sections
from orchestra.canon.types import JsonValue, Record
from orchestra.conductor.assignment import task_assignment
from orchestra.conductor.attention import AttentionItem, LandingFact, attention_items
from orchestra.conductor.effort_status import EffortStatus
from orchestra.conductor.effort_status import effort_statuses as _effort_statuses
from orchestra.conductor.landing import place_of_body
from orchestra.conductor.phase_progress import PhaseProgress, phase_counts
from orchestra.conductor.requirements import RequirementIndex, requirement_status
from orchestra.score.executor import (
    DEFAULT_SMALL_WAVE_BUDGET_MINUTES,
    task_executor,
)
from orchestra.score.lookups import current_phases
from orchestra.score.requirements import phase_requirements, requirement_lines
from orchestra.score.work_item_facts import (
    decision_choice,
    executor_task,
    record_scope,
    work_item_facts,
)
from orchestra.score.workflow_blockers import human_gates
from orchestra.tools import Merged, Unmerged, branch_state

FAILING_RESULT_VALUES = frozenset({"fail", "failed", "error"})
SUPPRESSED_FIELDS = frozenset({"subject", "owner"})

Predicate = Callable[[Record], bool]


class ViewError(Exception):
    pass


def _state(*states: str) -> Predicate:
    return lambda r: r.get("lifecycle_state") in states


def _all(*predicates: Predicate) -> Predicate:
    return lambda r: all(p(r) for p in predicates)


def _not_closed(record: Record) -> bool:
    return record_payload(record).get("status") != "closed"


def _payload_is(name: str, value: JsonValue) -> Predicate:
    return lambda r: record_payload(r).get(name) == value


def _payload_truthy(name: str) -> Predicate:
    return lambda r: bool(record_payload(r).get(name))


def _any(record: Record) -> bool:
    return True


@dataclass(frozen=True)
class Role:
    name: str
    record_type: str
    fields: tuple[str, ...]
    select: Predicate = _any
    own_group: bool = False
    gate: str | None = None


@dataclass(frozen=True)
class View:
    name: str
    title: str
    roles: tuple[Role, ...]
    group_by: str
    group_default: str | None = None
    order_by: str | None = None
    show_lifecycle_state: bool = False
    show_derived: tuple[str, ...] = ()
    show_assignment: bool = False
    show_phase_derived: bool = False
    effort_status: bool = False
    phase_derived_section: bool = False
    tally_type: str | None = None
    tally_field: str = "result"


GOAL = Role("goal", "score:effort", ("goal", "kind"), _all(_state("active"), _not_closed))
POSITION = Role(
    "position",
    "score:position",
    ("position", "scope"),
    _all(_state("active"), _not_closed),
)
ACCEPTANCE = Role(
    "acceptance",
    "score:acceptance",
    ("requirement", "method", "effort", "verify_command"),
    _state("active"),
)
FINDING_OPEN = Role(
    "finding",
    "tuner:finding",
    ("claim", "basis", "invalidated_when", "needs"),
    _state("asserted"),
)

GATE_ROLES = (
    Role(
        "blocking-question",
        "score:continuity-question",
        ("blocking", "scope"),
        gate="blocking-question",
    ),
    Role(
        "needs-human",
        "tuner:finding",
        ("claim", "needs"),
        gate="needs-human",
    ),
    Role(
        "unsigned-manual-check",
        "tuner:check-run",
        ("criterion_id", "result", "method", "signed_by"),
        gate="unsigned-check",
    ),
)

HANDOFF = View(
    "handoff",
    "Project Handoff",
    (
        GOAL,
        POSITION,
        Role("pending-phase-close", "score:phase", (), _state("in_progress")),
        Role(
            "latest-proof",
            "conductor:proof-packet",
            ("phase", "effort", "revision", "kind"),
            _state("recorded"),
        ),
        Role(
            "in-progress",
            "score:work-item",
            ("title", "phase", "kind", "effort"),
            _state("in_progress"),
        ),
        *GATE_ROLES,
        Role(
            "backlog",
            "composer:idea",
            ("effort", "status"),
            _all(
                _state("active"),
                _payload_is("status", "open"),
                _payload_truthy("effort"),
            ),
        ),
    ),
    group_by="effort",
    show_assignment=True,
    effort_status=True,
)

HOOK_ROLE_NAMES = (
    "goal",
    "position",
    "pending-phase-close",
    "in-progress",
    "blocking-question",
    "needs-human",
    "unsigned-manual-check",
)
HOOK_ROLES = tuple(role for role in HANDOFF.roles if role.name in HOOK_ROLE_NAMES)
HOOK_VIEW = replace(HANDOFF, roles=HOOK_ROLES, effort_status=False)

_WORK_FIELDS = ("title", "phase", "kind", "effort")

PLAN = View(
    "plan",
    "Project Plan",
    (
        Role(
            "phase",
            "score:phase",
            ("title", "ordinal", "effort"),
            _state("planned", "in_progress"),
        ),
        Role(
            "work",
            "score:work-item",
            _WORK_FIELDS,
            _state("planned", "in_progress"),
        ),
        ACCEPTANCE,
    ),
    group_by="phase",
    order_by="ordinal",
    show_assignment=True,
    show_phase_derived=True,
)

VERIFICATION = View(
    "verification",
    "Project Verification",
    (
        ACCEPTANCE,
        Role(
            "check",
            "tuner:check-run",
            ("criterion_id", "revision", "result", "method", "signed_by"),
        ),
        Role(
            "observation",
            "tuner:investigation-observation",
            ("what_was_observed", "effort"),
        ),
        FINDING_OPEN,
    ),
    group_by="subject",
    phase_derived_section=True,
)

STATUS = View(
    "status",
    "Project Status",
    (Role("work", "score:work-item", _WORK_FIELDS),),
    group_by="phase",
    order_by="ordinal",
    show_lifecycle_state=True,
    show_derived=("ready", "wave"),
    show_assignment=True,
    show_phase_derived=True,
    tally_type="tuner:check-run",
)

ROADMAP = View(
    "roadmap",
    "Project Roadmap",
    (
        Role("area", "composer:area", ("title",), _state("active"), own_group=True),
        Role(
            "idea",
            "composer:idea",
            ("status", "effort", "source"),
            _all(
                _state("active"),
                lambda r: record_payload(r).get("status") in ("open", "promoted"),
            ),
        ),
    ),
    group_by="area",
    group_default="untriaged",
)

VIEWS = {v.name: v for v in (HANDOFF, PLAN, VERIFICATION, STATUS, ROADMAP)}

EFFORT_TYPE = "score:effort"
WORK_ITEM_TYPE = "score:work-item"


def subject_related(parent: str, other: str) -> bool:
    if not parent or not other:
        return False
    if other == parent:
        return True
    if not other.startswith(parent):
        return False
    return not other[len(parent)].isalnum()


def _title(value: str) -> str:
    return " ".join(part.replace("-", " ").title() for part in value.split(":"))


def _display(value: JsonValue) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _empty(value: JsonValue) -> bool:
    return value is None or value == "" or value == []


def effort_of(record: Record) -> str | None:
    if record.get("record_type") == EFFORT_TYPE:
        return record.get("subject")
    payload = record_payload(record)
    value = payload.get("effort")
    return value if isinstance(value, str) and value else None


def _derived_value(record: Record, name: str) -> JsonValue:
    derived = record.get("derived")
    if derived is None:
        return None
    values: dict[str, JsonValue] = {}
    ready = derived.get("ready")
    if ready is not None:
        values["ready"] = ready
    wave = derived.get("wave")
    if wave is not None:
        values["wave"] = wave
    referenced_by = derived.get("referenced_by")
    if referenced_by is not None:
        references: dict[str, JsonValue] = {}
        for subject, ids in referenced_by.items():
            references[subject] = list(ids)
        values["referenced_by"] = references
    corrected = derived.get("corrected")
    if corrected is not None:
        values["corrected"] = corrected
    return values.get(name)


def _in_effort(record: Record, effort: str | None) -> bool:
    if effort is None:
        return True
    own = effort_of(record)
    if own is not None:
        return own == effort
    return record_payload(record).get("scope") == effort


def _group_key(record: Record, view: View, role: Role) -> str:
    payload = record_payload(record)
    group_by = view.group_by
    if role.own_group:
        return str(record.get("subject", "default"))
    if group_by == "scope":
        return str(payload.get("scope", "default"))
    if group_by == "subject":
        return str(record.get("subject", "default"))
    if view.group_default is not None and _empty(payload.get(group_by)):
        return view.group_default
    return str(payload.get(group_by, record.get("subject", "default")))


def _group_ordinal(name: str, order_field: str, records: list[Record]) -> int | None:
    candidates = sorted(
        (r for r in records if r.get("subject") == name), key=lambda r: r.get("id", "")
    )
    for candidate in candidates:
        value = record_payload(candidate).get(order_field)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def _group_sort_key(
    order_field: str | None, records: list[Record]
) -> Callable[[str], tuple[int, tuple[int, str] | tuple[str]]]:
    def key(name: str) -> tuple[int, tuple[int, str] | tuple[str]]:
        if order_field:
            ordinal = _group_ordinal(name, order_field, records)
            if ordinal is not None:
                return (0, (ordinal, name))
        return (1, (name,))

    return key


def _executor_bits(
    record: Record,
    records: list[Record],
    small_wave_budget_minutes: int,
) -> list[str]:
    phase = record_scope(record).phase
    wave = _derived_value(record, "wave")
    members = [
        candidate
        for candidate in records
        if candidate["record_type"] == WORK_ITEM_TYPE
        and candidate.get("lifecycle_state") == "planned"
        and record_scope(candidate).phase == phase
        and effort_of(candidate) == effort_of(record)
        and _derived_value(candidate, "wave") == wave
        and (wave is not None or candidate["id"] == record["id"])
    ]
    task = executor_task(record)
    assignment = task_assignment(record, records)
    if (
        record.get("lifecycle_state") in ("in_progress", "done")
        and assignment is not None
        and assignment.assignee in ("inline", "subagent")
    ):
        task = replace(task, assignee=assignment.assignee)
    mode = task_executor(
        task,
        [executor_task(candidate) for candidate in members] or [task],
        small_wave_budget_minutes=small_wave_budget_minutes,
    )
    planned = (
        record.get("lifecycle_state") == "planned"
        and task.assignee not in ("inline", "subagent")
        and not task.executor
    )
    prefix = "executor: predicted " if planned else "executor: "
    return [f"{prefix}{mode}"]


def _assignment_bits(
    record: Record,
    records: list[Record],
    small_wave_budget_minutes: int,
    show_executor: bool,
) -> list[str]:
    if record["record_type"] != WORK_ITEM_TYPE:
        return []
    assignment = task_assignment(record, records)
    bits: list[str] = []
    if assignment is not None and assignment.assignee:
        bits.append(f"assignee: {assignment.assignee}")
    if assignment is not None and assignment.write_root:
        bits.append(f"write root: {assignment.write_root}")
    if show_executor:
        bits.extend(_executor_bits(record, records, small_wave_budget_minutes))
    return bits


def _effort_pool(records: list[Record], effort: str | None) -> list[Record]:
    if effort is None:
        return records
    return [r for r in records if effort_of(r) in (None, effort)]


def _phase_derived_lines(
    records: list[Record],
    phase: str,
    effort: str | None = None,
    requirement_index: RequirementIndex | None = None,
    stage: PhaseProgress | None = None,
) -> list[str]:
    records = _effort_pool(records, effort)
    progress = phase_counts(records, phase)
    statuses = requirement_status(records, phase, index=requirement_index)
    stage_text = _stage_text(stage)
    if progress.total == 0 and not statuses and not stage_text:
        return []
    lines: list[str] = []
    if progress.total:
        counts = ", ".join(f"{state}: {count}" for state, count in progress.counts.items())
        lines += ["### Progress", f"- {progress.done}/{progress.total} done ({counts})"]
        if progress.in_progress:
            lines.append(f"- in progress: {', '.join(progress.in_progress)}")
        lines.append("")
    if statuses:
        lines.append("### Requirements")
        for requirement, status in statuses.items():
            suffix = f" _(assessment: {status.assessment_id})_" if status.assessment_id else ""
            lines.append(f"- **{requirement}**: {status.assessed or status.status}{suffix}")
        lines.append("")
    if stage_text:
        lines += ["### Stage", f"- {stage_text}", ""]
    return lines


def _stage_text(progress: PhaseProgress | None) -> str:
    if progress is None:
        return ""
    if progress.current is None:
        return progress.reason
    return f"{progress.current} ({progress.reason})" if progress.reason else progress.current


def _status_bits(
    record: Record,
    view: View,
    tally: list[Record],
    records: list[Record],
    small_wave_budget_minutes: int = DEFAULT_SMALL_WAVE_BUDGET_MINUTES,
) -> list[str]:
    bits: list[str] = []
    if view.show_lifecycle_state:
        bits.append(f"state: {record.get('lifecycle_state')}")
    for name in view.show_derived:
        value = _derived_value(record, name)
        if value is not None:
            bits.append(f"{name}: {value}")
    if view.show_assignment:
        bits.extend(
            _assignment_bits(
                record,
                records,
                small_wave_budget_minutes,
                show_executor=view.name == "plan",
            )
        )
    if view.tally_type:
        subject = record.get("subject", "")
        passed = failed = 0
        for candidate in tally:
            if not subject_related(subject, candidate.get("subject", "")):
                continue
            value = record_payload(candidate).get(view.tally_field)
            if not isinstance(value, str) or not value:
                continue
            if value.lower() in FAILING_RESULT_VALUES:
                failed += 1
            else:
                passed += 1
        bits.append(f"criteria: {passed} pass / {failed} fail")
    return bits


def _record_line(record: Record, role: Role, extra_bits: list[str], link: bool = True) -> str:
    payload = record_payload(record)
    bits: list[str] = []
    for name in role.fields:
        if name in SUPPRESSED_FIELDS:
            continue
        value = payload.get(name)
        if _empty(value):
            continue
        bits.append(_display(value))
    bits.extend(extra_bits)
    summary = "; ".join(bits)
    owner = payload.get("owner") if "owner" in role.fields else None
    if not link:
        note = f" _(owner: {owner})_" if owner else ""
        if summary:
            return f"- **{record['subject']}**: {summary}{note}"
        return f"- {record['subject']}{note}"
    extra = f"owner: {owner}, " if owner else ""
    ref = record["id"]
    if summary:
        return f"- **{record['subject']}**: {summary} _({extra}id: {ref})_"
    if owner:
        return f"- {record['subject']} _(owner: {owner}, id: {ref})_"
    return f"- {record['subject']} _(id: {ref})_"


def group_records(
    view: View, records: list[Record], effort: str | None
) -> dict[str, dict[str, list[Record]]]:
    scoped = [r for r in records if _in_effort(r, effort)]
    groups: dict[str, dict[str, list[Record]]] = {}
    gates: dict[str, list[Record]] | None = None
    for role in view.roles:
        if role.gate is None:
            picked = [r for r in scoped if r["record_type"] == role.record_type and role.select(r)]
        else:
            if gates is None:
                gates = {}
                for human_gate in human_gates(scoped):
                    gates.setdefault(human_gate.kind, []).append(human_gate.record)
            picked = [r for r in gates.get(role.gate, []) if r["record_type"] == role.record_type]
        for record in picked:
            if role.name == "pending-phase-close":
                progress = phase_counts(_effort_pool(scoped, effort_of(record)), record["subject"])
                if not progress.total or progress.done != progress.total:
                    continue
            key = _group_key(record, view, role)
            groups.setdefault(key, {r.name: [] for r in view.roles})
            groups[key][role.name].append(record)
    return groups


def group_lines(
    view: View,
    name: str,
    group: dict[str, list[Record]],
    tally: list[Record],
    records: list[Record],
    *,
    link: bool = True,
    effort: str | None = None,
    budget: int = DEFAULT_SMALL_WAVE_BUDGET_MINUTES,
    requirement_index: RequirementIndex | None = None,
    progress: Mapping[str, PhaseProgress] | None = None,
    status: str | None = None,
) -> list[str]:
    progress = progress or {}
    lines = [f"## {name}" if status is None else f"## {name} ({status})", ""]
    for role in view.roles:
        if status is not None and role.gate is not None:
            continue
        items = sorted(
            group.get(role.name) or [],
            key=lambda r: (r.get("subject", ""), r.get("id", "")),
        )
        if not items:
            continue
        lines.append(f"### {_title(role.name)}")
        for record in items:
            bits = _status_bits(record, view, tally, records, budget)
            if role.name == "pending-phase-close":
                stage_text = _stage_text(progress.get(record["subject"]))
                if stage_text:
                    bits.append(f"stage: {stage_text}")
            lines.append(_record_line(record, role, bits, link))
        lines.append("")
    if view.show_phase_derived:
        lines += _phase_derived_lines(records, name, effort, requirement_index, progress.get(name))
    return lines


def clock() -> datetime:
    override = os.environ.get("ORCHESTRA_NOW")
    if override:
        moment = datetime.fromisoformat(override.replace("Z", "+00:00"))
        return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def effort_statuses(records: list[Record], now: datetime | None = None) -> dict[str, EffortStatus]:
    return _effort_statuses(records, now or clock())


def landing_facts(records: list[Record], root: Path) -> dict[str, LandingFact]:
    facts: dict[str, LandingFact] = {}
    for subject, phase in current_phases(records).items():
        if phase["lifecycle_state"] != "done":
            continue
        place = place_of_body(subject, phase.get("body") or "", root)
        if place is None:
            continue
        state = branch_state(place.repo, place.branch, place.base)
        facts[subject] = LandingFact(
            exists=isinstance(state, (Merged, Unmerged)),
            merged=isinstance(state, Merged),
            branch=place.branch,
            ahead=state.ahead if isinstance(state, Unmerged) else 0,
        )
    return facts


_ATTENTION_TITLES = {"unsigned-check": "Unsigned Manual Check"}


def _attention_lines(item: AttentionItem) -> str:
    text = f": {item.text}" if item.text else ""
    return f"- **{item.subject}**{text} _(id: {item.record_id})_"


def render_view(
    view: View,
    records: list[Record],
    *,
    effort: str | None = None,
    statuses: Mapping[str, EffortStatus] | None = None,
    landing: Mapping[str, LandingFact] | None = None,
    progress: Mapping[str, PhaseProgress] | None = None,
) -> str:
    budget = DEFAULT_SMALL_WAVE_BUDGET_MINUTES
    if view.name == "plan":
        budget = load_project_config(Path.cwd()).small_wave_budget_minutes
    requirement_index = (
        RequirementIndex(_effort_pool(records, effort))
        if view.show_phase_derived or view.phase_derived_section
        else None
    )
    tally = [r for r in records if r["record_type"] == view.tally_type] if view.tally_type else []
    groups = group_records(view, records, effort)
    labels: Mapping[str, EffortStatus] = {}
    if view.effort_status:
        labels = statuses if statuses is not None else effort_statuses(records)
    for name in labels:
        if effort in (None, name):
            groups.setdefault(name, {})

    lines = [
        f"# {view.title}",
        "",
        "> Derived view — not authoritative. Edit underlying records, not this file.",
        "",
    ]
    if not groups:
        lines += ["_No matching records._", ""]
    for name in sorted(groups, key=_group_sort_key(view.order_by, records)):
        lines += group_lines(
            view,
            name,
            groups[name],
            tally,
            records,
            effort=effort,
            budget=budget,
            requirement_index=requirement_index,
            progress=progress,
            status=labels.get(name),
        )
        if name in labels:
            items = attention_items(records, name, landing or {})
            for kind in dict.fromkeys(item.kind for item in items):
                lines.append(f"### {_ATTENTION_TITLES.get(kind, _title(kind))}")
                lines += [_attention_lines(i) for i in items if i.kind == kind]
                lines.append("")
    if groups and view.phase_derived_section:
        lines += _phase_section_lines(groups, records, effort, requirement_index, progress or {})
    return "\n".join(lines)


def _phase_section_lines(
    groups: dict[str, dict[str, list[Record]]],
    records: list[Record],
    effort: str | None,
    requirement_index: RequirementIndex | None,
    progress: Mapping[str, PhaseProgress],
) -> list[str]:
    phases = sorted(
        {
            str(phase)
            for group in groups.values()
            for items in group.values()
            for record in items
            if (phase := record_payload(record).get("phase"))
        }
    )
    lines: list[str] = []
    for phase in phases:
        derived = _phase_derived_lines(
            records, phase, effort, requirement_index, progress.get(phase)
        )
        if derived:
            lines += [f"## Phase {phase}", "", *derived]
    return lines


BRIEF_ROLES = (
    Role("work", "score:work-item", _WORK_FIELDS, _state("planned", "in_progress")),
    ACCEPTANCE,
    FINDING_OPEN,
    Role(
        "constraint",
        "score:constraint",
        ("statement", "applies_to", "effort"),
        _state("active"),
    ),
    POSITION,
    Role("amendment", "conductor:assignment-amendment", ("assignment", "effort")),
)
_BRIEF_EFFORT_SCOPED = frozenset({"constraint", "position"})
_BRIEF_TITLES = {
    "work": "Work Item",
    "acceptance": "Acceptance Criteria",
    "finding": "Findings",
    "constraint": "Constraints",
    "position": "Position",
    "amendment": "Unapplied Amendments",
}


def _brief_in_scope(role: Role, subject: str, effort: str | None, record: Record) -> bool:
    if role.name == "work":
        return record.get("subject") == subject
    if role.name in _BRIEF_EFFORT_SCOPED:
        return record_scope(record).effort == effort
    return subject_related(subject, record.get("subject") or "")


def _brief_block(record: Record, role: Role) -> str:
    payload = record_payload(record)
    bits = [
        f"**{name}**: {_display(payload[name])}"
        for name in role.fields
        if not _empty(payload.get(name))
    ]
    if record.get("lifecycle_state"):
        bits.append(f"state: {record['lifecycle_state']}")
    lines = [f"### {record.get('subject')}"]
    if bits:
        lines.append("; ".join(bits))
    body = (record.get("body") or "").strip()
    if body:
        lines += ["", body]
    lines.append("")
    return "\n".join(lines)


def _phase_record(records: list[Record], record_type: str, phase: str | None) -> Record | None:
    return next(
        (
            r
            for r in records
            if r["record_type"] == record_type
            and r.get("lifecycle_state") == "active"
            and record_scope(r).phase == phase
        ),
        None,
    )


def _brief_acceptance_in_scope(work_item: Record, record: Record) -> bool:
    return record_scope(record) == record_scope(work_item)


def _orientation(work_item: Record, records: list[Record]) -> str:
    facts = work_item_facts(work_item)
    sections = body_sections(work_item.get("body") or "")
    lines = ["## Orientation", ""]
    for name, value in (("assignee", facts.assignee), ("write_root", facts.write_root)):
        if value is not None:
            lines.append(f"**{name}**: {_display(value)}")
    if len(lines) > 2:
        lines.append("")
    for name in ("Description", "Approach"):
        if sections.get(name):
            lines += [f"### Work item {name}", "", sections[name], ""]
    phase = facts.scope.phase
    spec_lines = {rid: f"{rid}: {text}" for rid, text in phase_requirements(records, phase or "")}
    description_lines = requirement_lines(sections.get("Description", ""))
    requirements = [
        spec_lines.get(rid) or description_lines.get(rid) or rid for rid in facts.requirements
    ]
    if requirements:
        lines += ["### Requirements", "", *(f"- {text}" for text in requirements), ""]
    design = _phase_record(records, "score:design", phase)
    if design:
        design_sections = body_sections(design.get("body") or "")
        for name in ("Invariants", "Assumptions"):
            if design_sections.get(name):
                lines += [f"### Design {name}", "", design_sections[name], ""]
    decisions: list[str] = []
    for name in facts.decisions:
        decision = next(
            (r for r in records if r["record_type"] == "score:decision" and r["subject"] == name),
            None,
        )
        choice = decision_choice(decision) if decision else None
        decisions.append(f"- {name}: {_display(choice)}" if not _empty(choice) else f"- {name}")
    if decisions:
        lines += ["### Decisions", "", *decisions, ""]
    if len(lines) == 2:
        lines += ["_None._", ""]
    return "\n".join(lines)


def render_brief(subject: str, records: list[Record]) -> str:
    work_role = BRIEF_ROLES[0]
    work_item = next(
        (
            r
            for r in records
            if r["record_type"] == work_role.record_type
            and r.get("subject") == subject
            and work_role.select(r)
        ),
        None,
    )
    if work_item is None:
        raise ViewError(f"no work item found for subject {subject!r}")
    effort = record_scope(work_item).effort
    sections: list[str] = [_orientation(work_item, records)]
    for role in BRIEF_ROLES:
        selected = sorted(
            (
                r
                for r in records
                if r["record_type"] == role.record_type
                and role.select(r)
                and _brief_in_scope(role, subject, effort, r)
                and (role.name != "acceptance" or _brief_acceptance_in_scope(work_item, r))
            ),
            key=lambda r: (r.get("subject") or "", r.get("id") or ""),
        )
        lines = [f"## {_BRIEF_TITLES.get(role.name, _title(role.name))}", ""]
        if selected:
            lines += [_brief_block(r, role) for r in selected]
        else:
            lines += ["_None._", ""]
        sections.append("\n".join(lines))
    return "\n".join(
        [
            f"# Brief: {subject}",
            "",
            "> Derived brief — not authoritative. Composed on demand by "
            "`orchestra brief`; edit records, not this output.",
            "",
            *sections,
        ]
    )


def load_records(project: Project) -> list[Record]:
    from orchestra.canon.derive import attach_derived_all

    return attach_derived_all(project.records(), project.derived())


def open_efforts(records: list[Record]) -> set[str]:
    return {name for name, status in effort_statuses(records).items() if status != "closed"}


def position_recorded_at(records: list[Record]) -> dict[str, str]:
    stamps: dict[str, str] = {}
    for r in records:
        if r["record_type"] != POSITION.record_type or not POSITION.select(r):
            continue
        effort = effort_of(r)
        stamp = r.get("recorded_at")
        if effort and stamp and record_payload(r).get("scope") == "effort":
            stamps[effort] = max(stamp, stamps.get(effort, ""))
    return stamps


def group_subjects(group: dict[str, list[Record]]) -> list[str]:
    return sorted({str(r.get("subject", "")) for items in group.values() for r in items})
