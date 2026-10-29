"""Markdown views rendered from canon records: handoff, plan, status, verification, brief."""

from __future__ import annotations

import posixpath
from dataclasses import dataclass, replace
from typing import Any, Callable

FAILING_RESULT_VALUES = frozenset({"fail", "failed", "error"})
STORE_ROOT = ".canon"
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


def _payload_truthy(name: str) -> Predicate:
    return lambda r: bool(_payload(r).get(name))


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
    own_group: bool = False


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
    tally_type: str | None = None
    tally_field: str = "result"


GOAL = Role(
    "goal", "score:effort", ("goal", "kind"), _all(_state("active"), _not_closed)
)
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

HANDOFF = View(
    "handoff",
    "Project Handoff",
    (
        GOAL,
        POSITION,
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
        Role(
            "blocking-question",
            "score:continuity-question",
            ("blocking", "scope"),
            _all(_state("open"), _payload_is("blocking", True)),
        ),
        Role(
            "needs-human",
            "tuner:finding",
            ("claim", "needs"),
            _all(
                _payload_is("needs", "human"),
                _state("asserted", "supported", "disputed"),
            ),
        ),
        Role(
            "unsigned-manual-check",
            "tuner:check-run",
            ("criterion_id", "result", "method", "signed_by"),
            _all(
                _payload_is("method", "manual"),
                _payload_is("signed_by", ""),
                lambda r: (r.get("derived") or {}).get("corrected") is not True,
            ),
        ),
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
)

HOOK_ROLE_NAMES = (
    "goal",
    "position",
    "in-progress",
    "blocking-question",
    "needs-human",
    "unsigned-manual-check",
)
HOOK_ROLES = tuple(role for role in HANDOFF.roles if role.name in HOOK_ROLE_NAMES)
HOOK_VIEW = replace(HANDOFF, roles=HOOK_ROLES)

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
)

STATUS = View(
    "status",
    "Project Status",
    (Role("work", "score:work-item", _WORK_FIELDS),),
    group_by="phase",
    order_by="ordinal",
    show_lifecycle_state=True,
    show_derived=("ready", "wave"),
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
                lambda r: _payload(r).get("status") in ("open", "promoted"),
            ),
        ),
    ),
    group_by="area",
    group_default="untriaged",
)

VIEWS = {v.name: v for v in (HANDOFF, PLAN, VERIFICATION, STATUS, ROADMAP)}

EFFORT_TYPE = "score:effort"


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


def _group_key(record: Record, view: View, role: Role) -> str:
    payload = _payload(record)
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


def _record_line(
    record: Record, role: Role, extra_bits: list[str], link: bool = True
) -> str:
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
    if not link:
        note = f" _(owner: {owner})_" if owner else ""
        if summary:
            return f"- **{record['subject']}**: {summary}{note}"
        return f"- {record['subject']}{note}"
    extra = f"owner: {owner}, " if owner else ""
    ref = f"[{record['id']}]({record_path(record)})"
    if summary:
        return f"- **{record['subject']}**: {summary} _({extra}id: {ref})_"
    if owner:
        return f"- {record['subject']} _(owner: {owner}, id: {ref})_"
    return f"- {record['subject']} _(id: {ref})_"


def _group_records(
    view: View, records: list[Record], effort: str | None
) -> dict[str, dict[str, list[Record]]]:
    scoped = [r for r in records if _in_effort(r, effort)]
    groups: dict[str, dict[str, list[Record]]] = {}
    for role in view.roles:
        for record in scoped:
            if record["record_type"] != role.record_type or not role.select(record):
                continue
            key = _group_key(record, view, role)
            groups.setdefault(key, {r.name: [] for r in view.roles})
            groups[key][role.name].append(record)
    return groups


def _group_lines(
    view: View,
    name: str,
    group: dict[str, list[Record]],
    tally: list[Record],
    *,
    link: bool = True,
) -> list[str]:
    lines = [f"## {name}", ""]
    for role in view.roles:
        items = sorted(
            group.get(role.name) or [],
            key=lambda r: (r.get("subject", ""), r.get("id", "")),
        )
        if not items:
            continue
        lines.append(f"### {_title(role.name)}")
        for record in items:
            lines.append(
                _record_line(record, role, _status_bits(record, view, tally), link)
            )
        lines.append("")
    return lines


def render_view(
    view: View, records: list[Record], *, effort: str | None = None
) -> str:
    tally = (
        [r for r in records if r["record_type"] == view.tally_type]
        if view.tally_type
        else []
    )
    groups = _group_records(view, records, effort)

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
        lines += _group_lines(view, name, groups[name], tally)
    return "\n".join(lines)


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
    from orchestra.canon.derive import attach_derived_all

    return attach_derived_all(project.records(), project.derived())


def live_efforts(records: list[Record]) -> set[str]:
    return {
        effort
        for role in (GOAL, POSITION)
        for r in records
        if r["record_type"] == role.record_type
        and role.select(r)
        and (effort := effort_of(r))
    }


def _position_recorded_at(records: list[Record]) -> dict[str, str]:
    stamps: dict[str, str] = {}
    for r in records:
        if r["record_type"] != POSITION.record_type or not POSITION.select(r):
            continue
        effort = effort_of(r)
        stamp = r.get("recorded_at")
        if effort and stamp and _payload(r).get("scope") == "effort":
            stamps[effort] = max(stamp, stamps.get(effort, ""))
    return stamps


def hook_handoff_sections(records: list[Record]) -> list[tuple[str, str]]:
    live = live_efforts(records)
    groups = {
        name: group
        for name, group in _group_records(HOOK_VIEW, records, None).items()
        if name in live
    }
    stamps = _position_recorded_at(records)
    stamped = sorted(n for n in groups if n in stamps)
    stamped.sort(key=stamps.__getitem__, reverse=True)
    unstamped = sorted(n for n in groups if n not in stamps)
    sections = []
    for name in (*stamped, *unstamped):
        lines = _group_lines(HOOK_VIEW, name, groups[name], [], link=False)
        sections.append((name, "\n".join(lines).rstrip()))
    return sections


def hook_constraints(records: list[Record], limit: int) -> tuple[list[Record], int]:
    live = live_efforts(records)
    role = next(r for r in BRIEF_ROLES if r.name == "constraint")
    matches = sorted(
        (
            r
            for r in records
            if r["record_type"] == role.record_type
            and role.select(r)
            and _payload(r).get("effort") in live
        ),
        key=lambda r: r.get("subject") or "",
    )
    return matches[:limit], len(matches)
