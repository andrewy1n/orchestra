from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from evals.seeded_defects.cases import Case, CaseSetError, load_case_set
from evals.seeded_defects.claude_call import CallResult, plan_calls, review_call
from evals.seeded_defects.outcomes import Complete, Incomplete, Outcome
from evals.seeded_defects.scoring import score_call
from orchestra.tools import RunFn

PROMPT_FILES = ("agents/reviewer.md", "orchestra/conductor/reviewer.py")
_CHECK_AFTER = 3
CASE_FILES = ("case.json", "defect.patch", "records.json", "baseline.json")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _case_set_hash(cases: list[Case], cases_dir: Path) -> str:
    digest = hashlib.sha256()
    for case in sorted(cases, key=lambda c: c.id):
        for name in CASE_FILES:
            path = cases_dir / case.id / name
            digest.update(f"{case.id}/{name}\0".encode())
            if path.is_file():
                digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)


def _outcome(result: CallResult) -> Outcome:
    if result.parsed is not None:
        return Complete(result.parsed)
    return Incomplete("unparsable")


def _saved_call(case: Case, call_index: int, result: CallResult) -> dict[str, object]:
    score = score_call(case, _outcome(result))
    return {
        "case_id": case.id,
        "call_index": call_index,
        "tokens": result.tokens,
        "incomplete_reason": result.incomplete_reason,
        "incomplete": score.incomplete,
        "verdict_catch": score.verdict_catch,
        "located_catch": score.located_catch,
        "false_alarm": score.false_alarm,
    }


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _check_resume(path: Path, expected: dict[str, object]) -> str | None:
    existing = json.loads(path.read_text())
    for key, value in expected.items():
        if existing.get(key) != value:
            return f"campaign {key} differs: saved {existing.get(key)!r}, now {value!r}"
    return None


def run_campaign(args: argparse.Namespace, run: RunFn, confirm: Callable[[str], bool]) -> int:
    repo: Path = args.repo
    cases_dir: Path = args.cases_dir
    campaign_dir: Path = args.campaign_dir
    try:
        cases = load_case_set(cases_dir, repo)
    except CaseSetError as exc:
        return _fail("\n".join(exc.errors))
    if args.cases:
        known = {case.id for case in cases}
        unknown = sorted(set(args.cases) - known)
        if unknown:
            return _fail(f"unknown case ids: {', '.join(unknown)}")
        cases = [case for case in cases if case.id in set(args.cases)]
    if _git(repo, "status", "--porcelain", "--", *PROMPT_FILES):
        return _fail("reviewer prompt files have uncommitted changes")
    prompt_commit = _git(repo, "log", "-1", "--format=%H", "--", *PROMPT_FILES)
    expected: dict[str, object] = {
        "model": args.model,
        "prompt_commit": prompt_commit,
        "case_set_hash": _case_set_hash(cases, cases_dir),
    }
    record = campaign_dir / "campaign.json"
    if record.is_file():
        mismatch = _check_resume(record, expected)
        if mismatch is not None:
            return _fail(mismatch)
    else:
        _write_json(record, expected)
    pending = [
        planned
        for planned in plan_calls(cases)
        if not (campaign_dir / "calls" / f"{planned.case.id}-{planned.call_index}.json").exists()
    ]
    if not pending:
        return 0
    if not confirm(f"The campaign will make {len(pending)} reviewer calls. Continue?"):
        return _fail("campaign declined before the first call")
    tokens_spent: list[int] = []
    for planned in pending:
        target = campaign_dir / "calls" / f"{planned.case.id}-{planned.call_index}.json"
        if len(tokens_spent) == _CHECK_AFTER:
            projected = sum(tokens_spent) // len(tokens_spent) * len(pending)
            if not confirm(
                f"After {_CHECK_AFTER} calls the projected total is {projected} tokens "
                f"for {len(pending)} calls. Continue?"
            ):
                return _fail("campaign declined after the first calls; saved results stay")
        result = review_call(
            planned.case,
            planned.call_index,
            str(args.model),
            run,
            case_dir=cases_dir / planned.case.id,
            source_repo=repo,
        )
        tokens_spent.append(result.tokens)
        if result.incomplete_reason == "usage_limit":
            return _fail("usage limit reached; resume the campaign later")
        if result.incomplete_reason == "failed":
            continue
        _write_json(target, _saved_call(planned.case, planned.call_index, result))
    return 0
