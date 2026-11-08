from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import TypeAlias

from orchestra.canon.types import JsonValue, Record
from orchestra.score.oracle_policy import resolve_oracle_policy
from orchestra.score.requirements import (
    acceptance_requirement_ids,
    phase_requirements,
    phase_weight,
    requirement_body_problems,
    requirements_in_body,
)
from orchestra.score.workflow_reviews import has_blocking_behavior_question

MARKER = "[NEEDS CLARIFICATION"
_CODE_SPAN = re.compile(r"`[^`]*`")
_COMPOUND = re.compile(r"\band\b|;")

RecordData: TypeAlias = Record


def _payload(record: RecordData) -> Mapping[str, JsonValue]:
    return record["payload"]


def _requirements(record: RecordData) -> list[str]:
    requirements = _payload(record).get("requirements")
    if not isinstance(requirements, list):
        return []
    result: list[str] = []
    for requirement in requirements:
        if isinstance(requirement, str):
            result.append(requirement)
    return result


def _recorded_at(record: RecordData) -> str:
    return record["recorded_at"]


def _body(record: RecordData) -> str:
    return record.get("body", "")


def _subject(record: RecordData) -> str:
    return record["subject"]


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    subject: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class Report:
    phase: str
    stage: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)


def _has_marker(body: str) -> bool:
    return MARKER in _CODE_SPAN.sub("", body)


def analyze_phase(records: Sequence[RecordData], phase: str, stage: str = "plan") -> Report:
    if stage not in ("spec", "design", "plan", "close"):
        raise ValueError(f"unknown analysis stage {stage!r}")

    def of_type(record_type: str, *states: str) -> list[RecordData]:
        return [
            r
            for r in records
            if r.get("record_type") == record_type
            and _payload(r).get("phase") == phase
            and r.get("lifecycle_state") in states
        ]

    report = Report(phase=phase, stage=stage)
    light = phase_weight(list(records), phase) == "light"
    specs = of_type("score:specification", "active")
    if not specs and not light:
        report.findings.append(
            Finding(
                "error",
                "active-specification-required",
                phase,
                "an active specification is required to analyze this phase",
            )
        )
        return report
    designs = of_type("score:design", "active")
    items = of_type("score:work-item", "planned", "in_progress", "done")
    acceptances = of_type("score:acceptance", "active")

    def add(severity: str, code: str, subject: str, message: str) -> None:
        report.findings.append(Finding(severity, code, subject, message))

    if light:
        subject = phase
        body_lines = phase_requirements(list(records), phase)
        listed = [rid for rid, _ in body_lines]
        marked = [
            r for r in records if r.get("record_type") == "score:phase" and _subject(r) == phase
        ]
        documents = marked
        for problem in requirement_body_problems(_body(marked[0]) if marked else ""):
            add("error", "light-requirements-invalid", subject, problem)
    else:
        spec = specs[0]
        subject = _subject(spec)
        listed = _requirements(spec)
        body_lines = requirements_in_body(_body(spec))
        body_ids = [rid for rid, _ in body_lines]
        for rid in listed:
            if rid not in body_ids:
                add(
                    "error",
                    "spec-id-not-in-body",
                    subject,
                    f"{rid} is listed in the specification but absent from ## Requirements",
                )
        for rid in dict.fromkeys(body_ids):
            if rid not in listed:
                add(
                    "error",
                    "body-id-not-in-spec",
                    subject,
                    f"{rid} is in ## Requirements but absent from the specification requirements",
                )
        if stage == "design" and not designs:
            add(
                "error",
                "active-design-required",
                phase,
                "an active design is required to analyze design",
            )
            return report
        documents = [spec] if stage == "spec" else [spec, *designs]

    if stage in ("spec", "design") and has_blocking_behavior_question(list(records), phase):
        add(
            "error",
            "blocking-behavior-question",
            phase,
            "a blocking behavior question keeps the specification unready",
        )

    if stage in ("plan", "close"):
        carried = {rid for item in items for rid in _requirements(item)}
        named = {
            rid for acceptance in acceptances for rid in acceptance_requirement_ids(acceptance)
        }
        for rid in listed:
            if rid not in carried:
                add(
                    "error",
                    "requirement-no-work-item",
                    subject,
                    f"{rid} is carried by no work-item",
                )
            if rid not in named:
                add(
                    "error",
                    "requirement-no-acceptance",
                    subject,
                    f"{rid} is named by no active acceptance",
                )

    source = "the phase body" if light else "the specification"
    for item in items:
        for rid in _requirements(item):
            if rid not in listed:
                add(
                    "error",
                    "work-item-unknown-requirement",
                    _subject(item),
                    f"work-item names {rid}, which {source} does not list",
                )
    phase_records = [
        r for r in records if r["record_type"] == "score:phase" and r["subject"] == phase
    ]
    phase_payload = _payload(max(phase_records, key=_recorded_at)) if phase_records else None
    for acceptance in acceptances:
        try:
            resolve_oracle_policy(_payload(acceptance), phase_payload)
        except ValueError as exc:
            add("error", "oracle-policy-invalid", _subject(acceptance), str(exc))
        ids = acceptance_requirement_ids(acceptance)
        for rid in ids:
            if rid not in listed:
                add(
                    "error",
                    "acceptance-unknown-requirement",
                    _subject(acceptance),
                    f"acceptance names {rid}, which {source} does not list",
                )
        if not light and (len(ids) > 1 or _payload(acceptance).get("requirements")):
            add(
                "error",
                "full-phase-multi-requirement",
                _subject(acceptance),
                "a full-phase acceptance names exactly one requirement",
            )

    for record in documents:
        if _has_marker(_body(record)):
            add(
                "error",
                "clarification-marker",
                _subject(record),
                f"{MARKER}] marker outside a code span",
            )

    for rid, text in body_lines:
        if _COMPOUND.search(_CODE_SPAN.sub("", text)):
            add(
                "warning",
                "compound-requirement",
                subject,
                f"{rid} joins clauses with 'and' or ';'",
            )

    if stage == "close":
        for acceptance in acceptances:
            runs = [
                r
                for r in records
                if r.get("record_type") == "tuner:check-run"
                and _payload(r).get("criterion_id") == acceptance.get("id")
            ]
            if not runs:
                add(
                    "error",
                    "acceptance-no-check-run",
                    _subject(acceptance),
                    f"acceptance {acceptance.get('id')} has no check-run",
                )
                continue
            latest = max(runs, key=_recorded_at)
            result = _payload(latest).get("result")
            if result != "pass":
                add(
                    "error",
                    "acceptance-not-passing",
                    _subject(acceptance),
                    f"acceptance {acceptance.get('id')} latest check-run result is {result!r}, not 'pass'",
                )

    return report
