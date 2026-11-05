#!/usr/bin/env python3
"""Count the store operations a phase cost, per record type and per task.

Usage:
    python3 scripts/ops_per_task.py <phase> [--max N] [--check-loop] [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from orchestra.canon import record_payload
from orchestra.canon.backend import open_backend
from orchestra.canon.project import Project, StoreBindingError, open_store
from orchestra.canon.types import Record
from orchestra.conductor.check import git_head
from orchestra.conductor.wave import closes_phase


def _text(record: Record, key: str) -> str:
    value = record_payload(record).get(key)
    return value if isinstance(value, str) else ""


def tasks_of(records: list[Record], phase: str) -> list[Record]:
    """One record per logical task: the active successor of any supersede chain."""
    chosen: dict[str, Record] = {}
    for r in records:
        if r["record_type"] != "score:work-item" or _text(r, "phase") != phase:
            continue
        current = chosen.get(r["subject"])
        rank = (r["lifecycle_state"] != "superseded", r["recorded_at"])
        if current is None or rank >= (
            current["lifecycle_state"] != "superseded",
            current["recorded_at"],
        ):
            chosen[r["subject"]] = r
    return [r for r in chosen.values() if r["lifecycle_state"] != "withdrawn"]


def belongs_to(
    record: Record, phase: str, acceptance_ids: set[str], task_subjects: set[str]
) -> bool:
    kind = record["record_type"]
    if kind == "tuner:check-run":
        return _text(record, "criterion_id") in acceptance_ids or record["subject"].startswith(
            phase + "-"
        )
    if kind == "conductor:execution-report":
        return _text(record, "work_item") in task_subjects
    return _text(record, "phase") == phase or (kind == "score:phase" and record["subject"] == phase)


def count_operations(project: Project, phase: str) -> tuple[Counter[str], int]:
    records = project.records()
    tasks = tasks_of(records, phase)
    subjects = {t["subject"] for t in tasks}
    acceptance_ids = {
        r["id"]
        for r in records
        if r["record_type"] == "score:acceptance" and _text(r, "phase") == phase
    }
    members = {
        r["id"]: r["record_type"] for r in records if belongs_to(r, phase, acceptance_ids, subjects)
    }
    counts: Counter[str] = Counter()
    for record_id, chain in open_backend(project.store_path).iter_chains():
        if record_id in members:
            counts[members[record_id]] += len(chain)
    return counts, len(tasks)


def _latest_by(records: list[Record], key: str) -> dict[str, Record]:
    latest: dict[str, Record] = {}
    for r in records:
        name = _text(r, key)
        if name and (name not in latest or r["recorded_at"] >= latest[name]["recorded_at"]):
            latest[name] = r
    return latest


def loop_problems(project: Project, phase: str, revision: str) -> list[str]:
    records = project.records()
    problems: list[str] = []
    phase_record = next(
        (r for r in records if r["record_type"] == "score:phase" and r["subject"] == phase), None
    )
    if phase_record is None:
        return [f"phase {phase!r} not found"]
    if _text(phase_record, "weight") != "light":
        problems.append("the phase is not light")
    for kind in ("score:specification", "score:design"):
        if any(r["record_type"] == kind and _text(r, "phase") == phase for r in records):
            problems.append(f"the phase has a {kind} record")
    tasks = tasks_of(records, phase)
    reports = _latest_by(
        [r for r in records if r["record_type"] == "conductor:execution-report"], "work_item"
    )
    for task in tasks:
        if task["lifecycle_state"] != "done":
            problems.append(f"task {task['subject']} is {task['lifecycle_state']}")
        report = reports.get(task["subject"])
        if report is None:
            problems.append(f"task {task['subject']} has no execution report")
        elif _text(report, "result") != "pass":
            problems.append(
                f"task {task['subject']} latest execution report is {_text(report, 'result')}"
            )
    closing = [t for t in tasks if closes_phase(t, tasks)]
    if not closing:
        problems.append("the phase has no closing verification task")
    elif not any(t["lifecycle_state"] == "done" for t in closing):
        problems.append("the closing verification task is not done")
    runs = [r for r in records if r["record_type"] == "tuner:check-run"]
    for acceptance in records:
        if (
            acceptance["record_type"] != "score:acceptance"
            or acceptance["lifecycle_state"] != "active"
            or _text(acceptance, "phase") != phase
        ):
            continue
        own = [r for r in runs if _text(r, "criterion_id") == acceptance["id"]]
        latest = max(own, key=lambda r: r["recorded_at"], default=None)
        if latest is None or _text(latest, "result") != "pass":
            problems.append(f"acceptance {acceptance['subject']} has no current passing check-run")
        elif _text(acceptance, "method") == "tdd" and not any(
            _text(r, "result") == "fail" and r["id"] != latest["id"] for r in own
        ):
            problems.append(f"tdd acceptance {acceptance['subject']} has no red check-run")
    reviews = [r for r in runs if r["subject"] == phase + "-review"]
    review = max(reviews, key=lambda r: r["recorded_at"], default=None)
    if review is None or _text(review, "result") != "pass":
        problems.append("the phase has no passing review check-run")
    elif _text(review, "revision") != revision:
        problems.append(
            f"the passing review is for {_text(review, 'revision')[:12]}, not {revision[:12]}"
        )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument("phase")
    parser.add_argument("--max", type=float, default=None, help="Fail above this per-task total")
    parser.add_argument(
        "--check-loop",
        action="store_true",
        help="Fail unless the recorded evidence shows the slim loop passed at --at",
    )
    parser.add_argument(
        "--at", default=None, help="Revision the review must cover (default: HEAD of the cwd)"
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        project = open_store(Path.cwd())
    except StoreBindingError as exc:
        print(f"ops_per_task: {exc}", file=sys.stderr)
        return 2
    counts, tasks = count_operations(project, args.phase)
    total = sum(counts.values())
    per_task = total / tasks if tasks else 0.0
    if args.json:
        print(
            json.dumps(
                {"phase": args.phase, "tasks": tasks, "counts": dict(counts), "per_task": per_task}
            )
        )
    else:
        for kind, count in sorted(counts.items()):
            print(f"{kind:32} {count:4} {count / tasks if tasks else 0:6.2f} per task")
        print(f"{'total':32} {total:4}")
        print(f"tasks: {tasks}")
        print(f"per task: {per_task:.1f}")
    if tasks == 0:
        print("ops_per_task: the phase has no work-items", file=sys.stderr)
        return 2
    status = 0
    if args.max is not None and per_task > args.max:
        print(f"ops_per_task: {per_task:.1f} per task exceeds {args.max:g}", file=sys.stderr)
        status = 1
    if args.check_loop:
        revision = args.at or git_head(Path.cwd())
        for problem in loop_problems(project, args.phase, revision):
            print(f"ops_per_task: {problem}", file=sys.stderr)
            status = 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
