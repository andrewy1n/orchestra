from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeAlias

from evals.seeded_defects.report import Report, compute_report
from orchestra.tools import RunFn

SubParsers: TypeAlias = "argparse._SubParsersAction[argparse.ArgumentParser]"  # pyright: ignore[reportPrivateUsage]
DEFAULT_CASES = Path(__file__).parent / "cases"
CaseResult: TypeAlias = "tuple[bool | None, int, int, int]"


def register(subparsers: SubParsers) -> None:
    parser = subparsers.add_parser("compare", help="compare two saved campaigns")
    parser.add_argument("campaign_a", type=Path)
    parser.add_argument("campaign_b", type=Path)
    parser.add_argument("--cases-dir", type=Path, default=DEFAULT_CASES)


def _read(path: Path) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
    data: dict[str, Any] = json.loads(path.read_text())  # pyright: ignore[reportExplicitAny]
    return data


def _case_results(campaign: Path) -> dict[str, CaseResult]:
    gate: dict[str, bool] = {}
    counts: dict[str, list[int]] = {}
    for path in sorted((campaign / "gate").glob("*.json")):
        data = _read(path)
        gate[str(data["case_id"])] = bool(data["caught"])
    for path in sorted((campaign / "calls").glob("*.json")):
        data = _read(path)
        if data["incomplete"]:
            continue
        row = counts.setdefault(str(data["case_id"]), [0, 0, 0])
        row[0] += bool(data["verdict_catch"])
        row[1] += bool(data["located_catch"])
        row[2] += bool(data["false_alarm"])
    return {
        case_id: (gate.get(case_id), *(counts.get(case_id) or [0, 0, 0]))  # pyright: ignore[reportReturnType]
        for case_id in sorted(set(gate) | set(counts))
    }


def _describe(result: CaseResult | None) -> str:
    if result is None:
        return "absent"
    caught, verdict, located, alarms = result
    gate = "n/a" if caught is None else str(caught).lower()
    return f"gate caught {gate}, verdict catches {verdict}, located catches {located}, false alarms {alarms}"


def _rate_lines(a: Report, b: Report) -> list[str]:
    lines = [f"incomplete calls: {a.incomplete_calls} | {b.incomplete_calls}"]

    def section(title: str, left: dict[str, str], right: dict[str, str]) -> None:
        lines.append(f"{title}:")
        for key in sorted(set(left) | set(right)):
            lines.append(f"  {key}: {left.get(key, 'absent')} | {right.get(key, 'absent')}")

    section("gate rate by kind", *(_strs(r.gate_by_kind) for r in (a, b)))
    section("gate rate by defect type", *(_strs(r.gate_by_type) for r in (a, b)))
    for attr in ("verdict", "located"):
        section(
            f"reviewer {attr} rate by kind",
            *({k: str(getattr(v, attr)) for k, v in r.reviewer_by_kind.items()} for r in (a, b)),
        )
        section(
            f"reviewer {attr} rate by defect type",
            *({k: str(getattr(v, attr)) for k, v in r.reviewer_by_type.items()} for r in (a, b)),
        )
    lines.append(f"false-alarm rate: {a.false_alarm} | {b.false_alarm}")
    lines.append(f"unstable cases: {a.unstable_cases} | {b.unstable_cases}")
    return lines


def _strs(rates: dict[str, Any]) -> dict[str, str]:  # pyright: ignore[reportExplicitAny]
    return {k: str(v) for k, v in rates.items()}


def run(args: argparse.Namespace, run: RunFn, confirm: Callable[[str], bool]) -> int:
    meta_a = _read(args.campaign_a / "campaign.json")
    meta_b = _read(args.campaign_b / "campaign.json")
    for field, label in (("model", "model"), ("case_set_hash", "case set hash")):
        if meta_a.get(field) != meta_b.get(field):
            print(
                f"refusing to compare: {label} is {meta_a.get(field)} in {args.campaign_a}"
                f" and {meta_b.get(field)} in {args.campaign_b}",
                file=sys.stderr,
            )
            return 1
    report_a = compute_report(args.campaign_a, args.cases_dir)
    report_b = compute_report(args.campaign_b, args.cases_dir)
    lines = [
        f"model: {meta_a.get('model')}",
        f"case set hash: {meta_a.get('case_set_hash')}",
        f"prompt commit A: {meta_a.get('prompt_commit')}",
        f"prompt commit B: {meta_b.get('prompt_commit')}",
        "rates, A | B",
        *_rate_lines(report_a, report_b),
    ]
    results_a = _case_results(args.campaign_a)
    results_b = _case_results(args.campaign_b)
    changed = [
        c for c in sorted(set(results_a) | set(results_b)) if results_a.get(c) != results_b.get(c)
    ]
    lines.append(f"cases that differ: {len(changed)}")
    for case_id in changed:
        lines.append(f"  {case_id}")
        lines.append(f"    A: {_describe(results_a.get(case_id))}")
        lines.append(f"    B: {_describe(results_b.get(case_id))}")
    print("\n".join(lines))
    return 0
