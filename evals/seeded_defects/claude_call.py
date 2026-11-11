from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from evals.seeded_defects.cases import Case
from evals.seeded_defects.trees import build_case_tree
from orchestra.conductor.reviewer import (
    ParsedReviewerOutput,
    ReviewerRecord,
    build_reviewer_brief,
    git_phase_diff,
    validate_reviewer_output,
)
from orchestra.tools import CliTool, JsonValue, RunFn, ToolError

CALLS_PER_CASE = 3
REVIEWER_AGENT = Path(__file__).resolve().parents[2] / "agents" / "reviewer.md"
USAGE_FIELDS = (
    "input_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "output_tokens",
)
USAGE_LIMIT = re.compile(r"usage limit", re.IGNORECASE)


class Claude(CliTool):
    executable = "claude"

    def review(self, brief: str, agents: str, model: str) -> str:
        self._check_version()
        args = [
            "--print",
            "--model",
            model,
            "--output-format",
            "json",
            "--agents",
            agents,
            "--agent",
            "reviewer",
            "--setting-sources",
            "user",
            "--no-session-persistence",
        ]
        return self._execute(args, brief).stdout


@dataclass(frozen=True)
class CallResult:
    parsed: ParsedReviewerOutput | None
    tokens: int
    incomplete_reason: str | None


@dataclass(frozen=True)
class PlannedCall:
    case: Case
    call_index: int


def plan_calls(cases: list[Case]) -> list[PlannedCall]:
    return [PlannedCall(case, index) for index in range(1, CALLS_PER_CASE + 1) for case in cases]


def _agents_json() -> str:
    text = REVIEWER_AGENT.read_text()
    _, frontmatter, body = text.split("---\n", 2)
    match = re.search(r"description: >-\n((?:[ \t]+.*\n?)+)", frontmatter)
    description = " ".join(match.group(1).split()) if match else ""
    definition = {
        "description": description,
        "prompt": body.strip(),
        "tools": ["Read", "Grep", "Glob", "Bash"],
    }
    return json.dumps({"reviewer": definition})


def _load_records(case_dir: Path) -> list[ReviewerRecord]:
    raw: JsonValue = json.loads((case_dir / "records.json").read_text())
    if not isinstance(raw, list):
        raise ValueError("records.json must be a list")
    return [item for item in raw if isinstance(item, dict)]


def _tokens(usage: JsonValue) -> int:
    if not isinstance(usage, dict):
        return 0
    return sum(
        value
        for name in USAGE_FIELDS
        if isinstance(value := usage.get(name), int) and not isinstance(value, bool)
    )


def _interpret(stdout: str) -> CallResult:
    try:
        envelope: JsonValue = json.loads(stdout)
    except ValueError:
        return CallResult(None, 0, "unparsable")
    if not isinstance(envelope, dict):
        return CallResult(None, 0, "unparsable")
    tokens = _tokens(envelope.get("usage"))
    result = envelope.get("result")
    text = result if isinstance(result, str) else ""
    if envelope.get("is_error") is True:
        return CallResult(None, tokens, "usage_limit" if USAGE_LIMIT.search(text) else "failed")
    try:
        return CallResult(validate_reviewer_output(text), tokens, None)
    except ValueError:
        return CallResult(None, tokens, "unparsable")


def review_call(
    case: Case,
    call_index: int,
    model: str,
    run: RunFn,
    *,
    case_dir: Path,
    source_repo: Path,
) -> CallResult:
    records = _load_records(case_dir)
    with tempfile.TemporaryDirectory() as scratch:
        tree = build_case_tree(source_repo, case.revision, case.patch, Path(scratch) / "tree")
        diff = git_phase_diff(tree, base="HEAD~1")
        brief = build_reviewer_brief(records=records, phase_diff=diff, base="HEAD~1")
        env = {**os.environ, "CANON_READONLY": "1"}
        tool = Claude(tree, run=run, timeout=1800.0, env=env)
        try:
            stdout = tool.review(brief, _agents_json(), model)
        except ToolError as error:
            limited = USAGE_LIMIT.search(f"{error} {error.stderr}") is not None
            return CallResult(None, 0, "usage_limit" if limited else "failed")
    return _interpret(stdout)
