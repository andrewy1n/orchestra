"""Markdown views rendered from canon records: handoff, plan, status, verification, brief."""

from __future__ import annotations

import posixpath
from dataclasses import dataclass
from typing import Any, Callable

FAILING_RESULT_VALUES = frozenset({"fail", "failed", "error"})
STORE_ROOT = ".artifacts"
SUPPRESSED_FIELDS = frozenset({"subject", "owner"})

Record = dict[str, Any]
Predicate = Callable[[Record], bool]


class ViewError(Exception):
    pass


def _payload(record: Record) -> dict[str, Any]:
    return record.get("payload") or {}


def _state(*states: str) -> Predicate:
    return lambda r: r.get("lifecycle_state") in states


def _all(*predicates: Predicate) -> Predicate:
    return lambda r: all(p(r) for p in predicates)


def _not_closed(record: Record) -> bool:
    return _payload(record).get("status") != "closed"


def _payload_is(name: str, value: Any) -> Predicate:
    return lambda r: _payload(r).get(name) == value


def _derived_is(name: str, value: Any) -> Predicate:
    return lambda r: (r.get("derived") or {}).get(name) == value


def _any(record: Record) -> bool:
    return True


@dataclass(frozen=True)
class Role:
    name: str
    record_type: str
    fields: tuple[str, ...]
    select: Predicate = _any


@dataclass(frozen=True)
class View:
    name: str
    title: str
    roles: tuple[Role, ...]
    group_by: str
    order_by: str | None = None
    show_lifecycle_state: bool = False
    show_derived: tuple[str, ...] = ()
    tally_type: str | None = None
    tally_field: str = "result"


GOAL = Role(
    "goal", "plan:effort", ("goal", "kind"), _all(_state("active"), _not_closed)
)
POSITION = Role(
    "position",
    "plan:position",
    ("position", "scope"),
    _all(_state("active"), _not_closed),
)
ACCEPTANCE = Role(
    "acceptance",
    "plan:acceptance",
    ("requirement", "method", "effort", "verify_command"),
    _state("active"),
)
FINDING_OPEN = Role(
    "finding",
    "aff:finding",
    ("claim", "basis", "invalidated_when", "needs"),
    _state("asserted"),
)

HANDOFF = View(
    "handoff",
    "Project Handoff",
    (
        GOAL,
        POSITION,
        Role(
            "latest-proof",
            "run:proof-packet",
            ("phase", "effort", "revision", "kind"),
            _state("recorded"),
        ),
        Role(
            "in-progress",
            "plan:work-item",
            ("title", "phase", "kind", "effort"),
            _state("in_progress"),
        ),
        Role(
            "blocking-question",
            "plan:continuity-question",
            ("blocking", "scope"),
            _all(_state("open"), _payload_is("blocking", True)),
        ),
        Role(
            "needs-human",
            "aff:finding",
            ("claim", "needs"),
            _all(
                _payload_is("needs", "human"),
                _state("asserted", "supported", "disputed"),
            ),
        ),
        Role(
            "unsigned-manual-check",
            "aff:check-run",
            ("criterion_id", "result", "method", "signed_by"),
            _all(
                _payload_is("method", "manual"),
                _payload_is("signed_by", ""),
                lambda r: (r.get("derived") or {}).get("corrected") is not True,
            ),
        ),
        Role(
            "backlog",
            "plan:backlog-item",
            ("effort", "status"),
            _all(_state("active"), _payload_is("status", "open")),
        ),
    ),
    group_by="effort",
)

_WORK_FIELDS = ("title", "phase", "kind", "effort")

PLAN = View(
    "plan",
    "Project Plan",
    (
        Role(
            "phase",
            "plan:phase",
            ("title", "ordinal", "effort"),
            _state("planned", "in_progress"),
        ),
        Role(
            "work",
            "plan:work-item",
            _WORK_FIELDS,
            _state("planned", "in_progress"),
        ),
        ACCEPTANCE,
    ),
    group_by="phase",
    order_by="ordinal",
)

VERIFICATION = View(
    "verification",
    "Project Verification",
    (
        ACCEPTANCE,
        Role(
            "check",
            "aff:check-run",
            ("criterion_id", "revision", "result", "method", "signed_by"),
        ),
        Role(
            "observation",
            "aff:investigation-observation",
            ("what_was_observed", "effort"),
        ),
        FINDING_OPEN,
    ),
    group_by="subject",
)

STATUS = View(
    "status",
    "Project Status",
    (Role("work", "plan:work-item", _WORK_FIELDS),),
    group_by="phase",
    order_by="ordinal",
    show_lifecycle_state=True,
    show_derived=("ready", "wave"),
    tally_type="aff:check-run",
)

VIEWS = {v.name: v for v in (HANDOFF, PLAN, VERIFICATION, STATUS)}

EFFORT_TYPE = "plan:effort"


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


def record_path(record: Record, store_root: str = STORE_ROOT) -> str:
    namespace, _, name = record["record_type"].partition(":")
    return posixpath.join(
        store_root, "records", f"{namespace}__{name}", f"{record['id']}.md"
    )


def _display(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _empty(value: Any) -> bool:
    return value is None or value == "" or value == []


def effort_of(record: Record) -> str | None:
    if record.get("record_type") == EFFORT_TYPE:
        return record.get("subject")
    payload = _payload(record)
    return payload.get("effort") or None


def _in_effort(record: Record, effort: str | None) -> bool:
    if effort is None:
        return True
    own = effort_of(record)
    if own is not None:
        return own == effort
    return _payload(record).get("scope") == effort


def _group_key(record: Record, group_by: str) -> str:
    payload = _payload(record)
    if group_by == "scope":
        return str(payload.get("scope", "default"))
    if group_by == "subject":
        return str(record.get("subject", "default"))
    return str(payload.get(group_by, record.get("subject", "default")))


def _group_ordinal(name: str, order_field: str, records: list[Record]) -> int | None:
    candidates = sorted(
        (r for r in records if r.get("subject") == name), key=lambda r: r.get("id", "")
    )
    for candidate in candidates:
        value = _payload(candidate).get(order_field)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def _group_sort_key(order_field: str | None, records: list[Record]):
    def key(name: str) -> tuple[int, Any]:
        if order_field:
            ordinal = _group_ordinal(name, order_field, records)
            if ordinal is not None:
                return (0, (ordinal, name))
        return (1, (name,))

    return key


def _status_bits(record: Record, view: View, tally: list[Record]) -> list[str]:
    bits = []
    if view.show_lifecycle_state:
        bits.append(f"state: {record.get('lifecycle_state')}")
    for name in view.show_derived:
        value = (record.get("derived") or {}).get(name)
        if value is not None:
            bits.append(f"{name}: {value}")
    if view.tally_type:
        subject = record.get("subject", "")
        passed = failed = 0
        for candidate in tally:
            if not subject_related(subject, candidate.get("subject", "")):
                continue
            value = _payload(candidate).get(view.tally_field)
            if not isinstance(value, str) or not value:
                continue
            if value.lower() in FAILING_RESULT_VALUES:
                failed += 1
            else:
                passed += 1
        bits.append(f"criteria: {passed} pass / {failed} fail")
    return bits


def _record_line(record: Record, role: Role, extra_bits: list[str]) -> str:
    payload = _payload(record)
    bits = []
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
    extra = f"owner: {owner}, " if owner else ""
    link = f"[{record['id']}]({record_path(record)})"
    if summary:
        return f"- **{record['subject']}**: {summary} _({extra}id: {link})_"
    if owner:
        return f"- {record['subject']} _(owner: {owner}, id: {link})_"
    return f"- {record['subject']} _(id: {link})_"


def render_view(
    view: View, records: list[Record], *, effort: str | None = None
) -> str:
    tally = (
        [r for r in records if r["record_type"] == view.tally_type]
        if view.tally_type
        else []
    )
    scoped = [r for r in records if _in_effort(r, effort)]
    groups: dict[str, dict[str, list[Record]]] = {}
    for role in view.roles:
        for record in scoped:
            if record["record_type"] != role.record_type or not role.select(record):
                continue
            key = _group_key(record, view.group_by)
            groups.setdefault(key, {r.name: [] for r in view.roles})
            groups[key][role.name].append(record)

    lines = [
        f"# {view.title}",
        "",
        "> Derived view — not authoritative. Edit underlying records, not this file.",
        "",
    ]
    if not groups:
        lines += ["_No matching records._", ""]
        return "\n".join(lines)
    for name in sorted(groups, key=_group_sort_key(view.order_by, records)):
        lines += [f"## {name}", ""]
        for role in view.roles:
            items = sorted(
                groups[name].get(role.name) or [],
                key=lambda r: (r.get("subject", ""), r.get("id", "")),
            )
            if not items:
                continue
            lines.append(f"### {_title(role.name)}")
            for record in items:
                lines.append(_record_line(record, role, _status_bits(record, view, tally)))
            lines.append("")
    return "\n".join(lines)


BRIEF_ROLES = (
    Role("work", "plan:work-item", _WORK_FIELDS, _state("planned", "in_progress")),
    ACCEPTANCE,
    FINDING_OPEN,
    Role(
        "constraint",
        "plan:constraint",
        ("statement", "applies_to", "effort"),
        _state("active"),
    ),
    POSITION,
    Role("amendment", "run:assignment-amendment", ("assignment", "effort")),
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


def _brief_in_scope(role: Role, subject: str, effort: str, record: Record) -> bool:
    if role.name == "work":
        return record.get("subject") == subject
    if role.name in _BRIEF_EFFORT_SCOPED:
        return _payload(record).get("effort") == effort
    return subject_related(subject, record.get("subject") or "")


def _brief_block(record: Record, role: Role) -> str:
    payload = _payload(record)
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
    effort = _payload(work_item).get("effort", "")
    sections = []
    for role in BRIEF_ROLES:
        selected = sorted(
            (
                r
                for r in records
                if r["record_type"] == role.record_type
                and role.select(r)
                and _brief_in_scope(role, subject, effort, r)
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


def load_records(project: Any) -> list[Record]:
    from canon.derive import attach_derived_all

    return attach_derived_all(project.records(), project.derived())


def hook_constraints(records: list[Record], limit: int) -> tuple[list[Record], int]:
    effort = next(
        (
            _payload(r).get("effort")
            for r in records
            if r["record_type"] == POSITION.record_type
            and POSITION.select(r)
            and _payload(r).get("effort")
        ),
        None,
    )
    if not effort:
        return [], 0
    role = next(r for r in BRIEF_ROLES if r.name == "constraint")
    matches = sorted(
        (
            r
            for r in records
            if r["record_type"] == role.record_type
            and role.select(r)
            and _payload(r).get("effort") == effort
        ),
        key=lambda r: r.get("subject") or "",
    )
    return matches[:limit], len(matches)
