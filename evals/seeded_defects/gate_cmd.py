from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeAlias

from evals.seeded_defects.cases import Case, CaseSetError, load_case_set
from evals.seeded_defects.trees import build_case_tree
from orchestra.tools import RunFn

SubParsers: TypeAlias = "argparse._SubParsersAction[argparse.ArgumentParser]"  # pyright: ignore[reportPrivateUsage]
COMMAND_TIMEOUT_SECONDS = 600


def register(subparsers: SubParsers) -> None:
    parser = subparsers.add_parser("gate", help="run the gate tier on a case set")
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--campaign-dir", type=Path, required=True)


def _read_json(path: Path) -> Any:  # pyright: ignore[reportExplicitAny]
    return json.loads(path.read_text())


def _verify_commands(case_folder: Path) -> list[tuple[str, str]]:
    raw = _read_json(case_folder / "records.json")
    return [(str(e["subject"]), str(e["verify_command"])) for e in raw["acceptances"]]


def _passes(command: str, tree: Path) -> bool:
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=tree,
            capture_output=True,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return False
    return result.returncode == 0


def _gate_case(case: Case, case_folder: Path, repo: Path) -> dict[str, object]:
    baseline = _read_json(case_folder / "baseline.json")
    commands: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory() as scratch:
        tree = build_case_tree(repo, case.revision, case.patch, Path(scratch) / "tree")
        for subject, command in _verify_commands(case_folder):
            passed = _passes(command, tree)
            base = baseline.get(command, "fail")
            commands.append(
                {
                    "subject": subject,
                    "command": command,
                    "baseline": base,
                    "result": "pass" if passed else "fail",
                    "counted": base == "pass",
                }
            )
    caught = any(c["counted"] and c["result"] == "fail" for c in commands)
    return {"case_id": case.id, "caught": caught, "commands": commands}


def run(args: argparse.Namespace, run: RunFn, confirm: Callable[[str], bool]) -> int:
    cases_dir: Path = args.cases
    try:
        cases = load_case_set(cases_dir, args.repo)
    except CaseSetError as exc:
        for error in exc.errors:
            print(error, file=sys.stderr)
        return 1
    out = Path(args.campaign_dir) / "gate"
    out.mkdir(parents=True, exist_ok=True)
    for case in cases:
        report = _gate_case(case, cases_dir / case.id, args.repo)
        (out / f"{case.id}.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0
