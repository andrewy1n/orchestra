from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

MARKER = "[NEEDS CLARIFICATION"
_CODE_SPAN = re.compile(r"`[^`]*`")
_REQUIREMENT_LINE = re.compile(r"^(R\d+):\s*(.*)$")
_COMPOUND = re.compile(r"\band\b|;")


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
    skipped: bool = False
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)


def _requirements_section(body: str) -> list[tuple[str, str]]:
    lines: list[str] = []
    inside = False
    for line in body.splitlines():
        if line.startswith("## "):
            inside = line[3:].strip() == "Requirements"
        elif inside:
            lines.append(line.strip())
    matches = (_REQUIREMENT_LINE.match(line) for line in lines)
    return [(m.group(1), m.group(2)) for m in matches if m]


def _has_marker(body: str) -> bool:
    return MARKER in _CODE_SPAN.sub("", body)


def analyze_phase(records: list[dict[str, Any]], phase: str, stage: str = "plan") -> Report:
    def of_type(record_type: str, *states: str) -> list[dict[str, Any]]:
        return [
            r for r in records
            if r.get("record_type") == record_type
            and (r.get("payload") or {}).get("phase") == phase
            and r.get("lifecycle_state") in states
        ]

    report = Report(phase=phase, stage=stage)
    specs = of_type("score:specification", "active")
    if not specs:
        report.skipped = True
        return report
    spec = specs[0]
    designs = of_type("score:design", "active")
    items = of_type("score:work-item", "planned", "in_progress", "done")
    acceptances = of_type("score:acceptance", "active")

    def add(severity: str, code: str, subject: str, message: str) -> None:
        report.findings.append(Finding(severity, code, subject, message))

    spec_subject = spec["subject"]
    listed = list(spec["payload"].get("requirements") or [])
    body_lines = _requirements_section(spec.get("body") or "")
    body_ids = [rid for rid, _ in body_lines]

    for rid in listed:
        if rid not in body_ids:
            add("error", "spec-id-not-in-body", spec_subject, f"{rid} is listed in the specification but absent from ## Requirements")
    for rid in dict.fromkeys(body_ids):
        if rid not in listed:
            add("error", "body-id-not-in-spec", spec_subject, f"{rid} is in ## Requirements but absent from the specification requirements")

    carried = {rid for item in items for rid in item["payload"].get("requirements") or []}
    named = {a["payload"].get("requirement") for a in acceptances}
    for rid in listed:
        if rid not in carried:
            add("error", "requirement-no-work-item", spec_subject, f"{rid} is carried by no work-item")
        if rid not in named:
            add("error", "requirement-no-acceptance", spec_subject, f"{rid} is named by no active acceptance")

    for item in items:
        for rid in item["payload"].get("requirements") or []:
            if rid not in listed:
                add("error", "work-item-unknown-requirement", item["subject"], f"work-item names {rid}, which the specification does not list")
    for acceptance in acceptances:
        rid = acceptance["payload"].get("requirement")
        if rid and rid not in listed:
            add("error", "acceptance-unknown-requirement", acceptance["subject"], f"acceptance names {rid}, which the specification does not list")

    for record in (spec, *designs):
        if _has_marker(record.get("body") or ""):
            add("error", "clarification-marker", record["subject"], f"{MARKER}] marker outside a code span")

    for rid, text in body_lines:
        if _COMPOUND.search(_CODE_SPAN.sub("", text)):
            add("warning", "compound-requirement", spec_subject, f"{rid} joins clauses with 'and' or ';'")

    if stage == "close":
        for acceptance in acceptances:
            runs = [
                r for r in records
                if r.get("record_type") == "tuner:check-run"
                and (r.get("payload") or {}).get("criterion_id") == acceptance["id"]
            ]
            if not runs:
                add("error", "acceptance-no-check-run", acceptance["subject"], f"acceptance {acceptance['id']} has no check-run")
                continue
            latest = max(runs, key=lambda r: r.get("recorded_at") or "")
            result = latest["payload"].get("result")
            if result != "pass":
                add("error", "acceptance-not-passing", acceptance["subject"], f"acceptance {acceptance['id']} latest check-run result is {result!r}, not 'pass'")

    return report
