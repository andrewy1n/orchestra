from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from evals.seeded_defects.cases import DEFECT_KINDS, DEFECT_TYPES, KINDS


@dataclass(frozen=True)
class Rate:
    hits: int
    total: int

    @property
    def value(self) -> float | None:
        return None if self.total == 0 else self.hits / self.total

    def __str__(self) -> str:
        if self.total == 0:
            return "n/a (0/0)"
        return f"{self.hits}/{self.total} ({100 * self.hits / self.total:.1f}%)"


@dataclass(frozen=True)
class ReviewerRates:
    verdict: Rate
    located: Rate


@dataclass(frozen=True)
class Report:
    incomplete_calls: int = 0
    gate_by_kind: dict[str, Rate] = field(default_factory=lambda: {})
    gate_by_type: dict[str, Rate] = field(default_factory=lambda: {})
    reviewer_by_kind: dict[str, ReviewerRates] = field(default_factory=lambda: {})
    reviewer_by_type: dict[str, ReviewerRates] = field(default_factory=lambda: {})
    false_alarm: Rate = Rate(0, 0)
    unstable_cases: int = 0
    case_lines: tuple[str, ...] = ()
    call_tokens: tuple[tuple[str, int, int], ...] = field(default=(), compare=False)
    total_tokens: int = field(default=0, compare=False)


@dataclass(frozen=True)
class CaseInfo:
    id: str
    kind: str
    defect_type: str | None


def _read(path: Path) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
    raw: Any = json.loads(path.read_text())  # pyright: ignore[reportExplicitAny]
    return raw if isinstance(raw, dict) else {}  # pyright: ignore[reportUnknownVariableType]


def _read_cases(cases_dir: Path) -> list[CaseInfo]:
    cases: list[CaseInfo] = []
    for folder in sorted(p for p in cases_dir.iterdir() if p.is_dir()):
        meta = _read(folder / "case.json")
        kind = meta.get("kind")
        defect_type = meta.get("defect_type")
        if kind in KINDS:
            cases.append(
                CaseInfo(
                    folder.name,
                    str(kind),
                    str(defect_type) if defect_type in DEFECT_TYPES else None,
                )
            )
    return cases


def _read_dir(directory: Path) -> list[dict[str, Any]]:  # pyright: ignore[reportExplicitAny]
    if not directory.is_dir():
        return []
    return [_read(p) for p in sorted(directory.glob("*.json"))]


def _ordered(keys: set[str], order: tuple[str, ...]) -> list[str]:
    return [key for key in order if key in keys]


def compute_report(campaign_dir: Path, cases_dir: Path) -> Report:
    cases = {case.id: case for case in _read_cases(cases_dir)}
    calls = _read_dir(campaign_dir / "calls")
    gates = {
        str(g.get("case_id")): g.get("caught") is True for g in _read_dir(campaign_dir / "gate")
    }
    complete: dict[str, list[dict[str, Any]]] = {}  # pyright: ignore[reportExplicitAny]
    incomplete = 0
    for call in calls:
        case_id = str(call.get("case_id"))
        if case_id not in cases:
            continue
        if call.get("incomplete") is True:
            incomplete += 1
        else:
            complete.setdefault(case_id, []).append(call)

    defects = [c for c in cases.values() if c.kind in DEFECT_KINDS]

    def gate_rate(group: list[CaseInfo]) -> Rate:
        seen = [c for c in group if c.id in gates]
        return Rate(sum(gates[c.id] for c in seen), len(seen))

    def reviewer_rate(group: list[CaseInfo]) -> ReviewerRates:
        made = [call for c in group for call in complete.get(c.id, [])]
        return ReviewerRates(
            Rate(sum(call.get("verdict_catch") is True for call in made), len(made)),
            Rate(sum(call.get("located_catch") is True for call in made), len(made)),
        )

    kinds = _ordered({c.kind for c in defects}, KINDS)
    types = _ordered({c.defect_type for c in defects if c.defect_type}, DEFECT_TYPES)  # pyright: ignore[reportArgumentType]
    by_kind = {k: [c for c in defects if c.kind == k] for k in kinds}
    by_type = {t: [c for c in defects if c.defect_type == t] for t in types}

    control_calls = [
        call for c in cases.values() if c.kind == "control" for call in complete.get(c.id, [])
    ]
    unstable = 0
    for case in cases.values():
        made = complete.get(case.id, [])
        if len(made) != 3:
            continue
        key = "false_alarm" if case.kind == "control" else "verdict_catch"
        if len({made_call.get(key) is True for made_call in made}) > 1:
            unstable += 1

    def gate_text(case_id: str) -> str:
        if case_id not in gates:
            return "n/a"
        return "caught" if gates[case_id] else "missed"

    case_lines: list[str] = []
    for case in sorted(cases.values(), key=lambda c: c.id):
        rates = reviewer_rate([case])
        if case.kind == "control":
            made = complete.get(case.id, [])
            alarms = Rate(sum(call.get("false_alarm") is True for call in made), len(made))
            detail = f"false alarms {alarms}"
        else:
            detail = f"verdict {rates.verdict}, located {rates.located}"
        case_lines.append(f"case {case.id}: gate {gate_text(case.id)}, {detail}")

    def as_int(value: object) -> int:
        return value if isinstance(value, int) and not isinstance(value, bool) else 0

    call_tokens = sorted(
        (str(call.get("case_id")), as_int(call.get("call_index")), as_int(call.get("tokens")))
        for call in calls
        if str(call.get("case_id")) in cases
    )

    return Report(
        incomplete_calls=incomplete,
        gate_by_kind={k: gate_rate(g) for k, g in by_kind.items()},
        gate_by_type={t: gate_rate(g) for t, g in by_type.items()},
        reviewer_by_kind={k: reviewer_rate(g) for k, g in by_kind.items()},
        reviewer_by_type={t: reviewer_rate(g) for t, g in by_type.items()},
        false_alarm=Rate(
            sum(call.get("false_alarm") is True for call in control_calls), len(control_calls)
        ),
        unstable_cases=unstable,
        case_lines=tuple(case_lines),
        call_tokens=tuple(call_tokens),
        total_tokens=sum(tokens for _, _, tokens in call_tokens),
    )


def format_report(report: Report) -> str:
    lines: list[str] = []
    if report.incomplete_calls:
        lines.append(f"incomplete calls: {report.incomplete_calls}")
    lines.append("gate catch rate by kind:")
    lines += [f"  {k}: {r}" for k, r in report.gate_by_kind.items()]
    lines.append("gate catch rate by defect type:")
    lines += [f"  {t}: {r}" for t, r in report.gate_by_type.items()]
    lines.append("reviewer verdict rate by kind:")
    lines += [f"  {k}: {r.verdict}" for k, r in report.reviewer_by_kind.items()]
    lines.append("reviewer verdict rate by defect type:")
    lines += [f"  {t}: {r.verdict}" for t, r in report.reviewer_by_type.items()]
    lines.append("reviewer located rate by kind:")
    lines += [f"  {k}: {r.located}" for k, r in report.reviewer_by_kind.items()]
    lines.append("reviewer located rate by defect type:")
    lines += [f"  {t}: {r.located}" for t, r in report.reviewer_by_type.items()]
    lines.append(f"false-alarm rate: {report.false_alarm}")
    lines.append(f"unstable cases: {report.unstable_cases}")
    lines += report.case_lines
    lines += [
        f"tokens {case_id} call {index}: {tokens}" for case_id, index, tokens in report.call_tokens
    ]
    lines.append(f"tokens total: {report.total_tokens}")
    return "\n".join(lines) + "\n"


def build_header(campaign_dir: Path) -> str:
    record = campaign_dir / "campaign.json"
    if not record.is_file():
        return ""
    meta = _read(record)
    return (
        f"model: {meta.get('model')}\n"
        f"reviewer prompt commit: {meta.get('prompt_commit')}\n"
        f"case set hash: {meta.get('case_set_hash')}\n"
    )


def build_report(campaign_dir: Path, cases_dir: Path) -> str:
    return format_report(compute_report(campaign_dir, cases_dir))
