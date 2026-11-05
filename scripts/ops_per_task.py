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


def _text(record: Record, key: str) -> str:
    value = record_payload(record).get(key)
    return value if isinstance(value, str) else ""


def tasks_of(records: list[Record], phase: str) -> list[Record]:
    return [
        r
        for r in records
        if r["record_type"] == "score:work-item"
        and r["lifecycle_state"] != "withdrawn"
        and _text(r, "phase") == phase
    ]


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


def loop_problems(project: Project, phase: str) -> list[str]:
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
    reports = {
        _text(r, "work_item") for r in records if r["record_type"] == "conductor:execution-report"
    }
    for task in tasks:
        if task["lifecycle_state"] != "done":
            problems.append(f"task {task['subject']} is {task['lifecycle_state']}")
        if task["subject"] not in reports:
            problems.append(f"task {task['subject']} has no execution report")
    reviews = [
        r
        for r in records
        if r["record_type"] == "tuner:check-run" and r["subject"] == phase + "-review"
    ]
    latest = max(reviews, key=lambda r: r["recorded_at"], default=None)
    if latest is None or _text(latest, "result") != "pass":
        problems.append("the phase has no passing review check-run")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument("phase")
    parser.add_argument("--max", type=float, default=None, help="Fail above this per-task total")
    parser.add_argument("--check-loop", action="store_true", help="Fail unless the slim loop ran")
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
        for problem in loop_problems(project, args.phase):
            print(f"ops_per_task: {problem}", file=sys.stderr)
            status = 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
