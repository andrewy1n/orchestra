from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, overload

import pytest

from evals.seeded_defects.cases import Case
from evals.seeded_defects.claude_call import CallResult, Claude, plan_calls, review_call
from orchestra.tools.testing import ScriptedRun

FIXTURE = Path(__file__).parent / "fixtures" / "claude_haiku_review.json"
REPO_ROOT = Path(__file__).resolve().parents[2]

REVIEW_TEXT = (
    "verdict: NEEDS_WORK\n"
    "findings:\n"
    "  - task: t1\n"
    "    kind: behavior-bug\n"
    "    expected: a\n"
    "    observed: b\n"
    "    severity: major\n"
    "    blocking: true\n"
    "    requirement: r\n"
    "    trigger: x\n"
    "    consequence: y\n"
    "integration:\n"
    "  interfaces: i\n"
    "  assumptions: a\n"
    "  invariants: v\n"
    "  conflicts:\n"
)


def envelope(result: str, *, is_error: bool = False, usage: Mapping[str, int] | None = None) -> str:
    return json.dumps(
        {
            "type": "result",
            "is_error": is_error,
            "result": result,
            "usage": dict(
                usage
                or {
                    "input_tokens": 10,
                    "cache_creation_input_tokens": 200,
                    "cache_read_input_tokens": 3000,
                    "output_tokens": 40,
                }
            ),
        }
    )


class Recording(ScriptedRun):
    def __init__(self, *replies: str | Exception) -> None:
        super().__init__(Claude, {}, Claude.min_version)
        self.replies: list[str | Exception] = list(replies)
        self.inputs: list[str | bytes | None] = []
        self.cwds: list[Path] = []

    @overload
    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        input: str | None,
        timeout: float | None,
        capture_output: bool,
        text: Literal[True],
        check: bool,
        env: Mapping[str, str] | None,
    ) -> subprocess.CompletedProcess[str]: ...

    @overload
    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        input: bytes | None,
        timeout: float | None,
        capture_output: bool,
        text: Literal[False],
        check: bool,
        env: Mapping[str, str] | None,
    ) -> subprocess.CompletedProcess[bytes]: ...

    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        input: str | bytes | None,
        timeout: float | None,
        capture_output: bool,
        text: bool,
        check: bool,
        env: Mapping[str, str] | None,
    ) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
        if tuple(argv[1:]) != ("--version",):
            self.inputs.append(input)
            self.cwds.append(cwd)
            reply = self.replies.pop(0)
            if isinstance(reply, Exception):
                raise reply
            self._responses[tuple(argv)] = reply
        return super().__call__(  # pyright: ignore[reportCallIssue] -- the overloads need literal text and typed input
            argv,
            cwd=cwd,
            input=input,  # pyright: ignore[reportArgumentType] -- input type follows text
            timeout=timeout,
            capture_output=capture_output,
            text=text,  # pyright: ignore[reportArgumentType] -- text is a plain bool here
            check=check,
            env=env,
        )

    def claude_calls(self) -> list[tuple[str, ...]]:
        return [call for call in self.calls if call[1:] != ("--version",)]


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def source(tmp_path: Path) -> tuple[Path, str]:
    path = tmp_path / "source"
    path.mkdir()
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "t@example.com")
    git(path, "config", "user.name", "t")
    (path / "a.txt").write_text("one\n")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "base")
    (path / "a.txt").write_text("one\ntwo\n")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "landing")
    return path, git(path, "rev-parse", "HEAD")


RECORDS = [
    {
        "record_type": "work-item",
        "subject": "wi-1",
        "title": "Add two",
        "body": "WORKITEM-BODY",
    },
    {
        "record_type": "acceptance",
        "subject": "wi-1",
        "criterion": "ACCEPT-CRITERION",
        "body": "",
    },
    {"record_type": "execution-report", "subject": "wi-1", "body": "SELF-GRADE-SECRET"},
]


def make_case(tmp_path: Path, revision: str, case_id: str = "c1") -> tuple[Case, Path]:
    folder = tmp_path / "cases" / case_id
    folder.mkdir(parents=True)
    (folder / "records.json").write_text(json.dumps(RECORDS))
    case = Case(
        id=case_id,
        phase="p1",
        revision=revision,
        kind="control",
        defect_type=None,
        patch=None,
        expected_files=frozenset(),
        expected_requirement_ids=frozenset(),
    )
    return case, folder


def cases_of(n: int) -> list[Case]:
    return [
        Case(f"case-{i}", "p", "rev", "control", None, None, frozenset(), frozenset())
        for i in range(n)
    ]


def test_three_calls_per_case() -> None:
    cases = cases_of(4)
    planned = plan_calls(cases)
    assert len(planned) == 12
    for case in cases:
        assert sorted(p.call_index for p in planned if p.case is case) == [1, 2, 3]


def test_three_calls_per_case_ordered_by_call_index_then_case() -> None:
    cases = cases_of(2)
    planned = plan_calls(cases)
    assert [(p.call_index, p.case.id) for p in planned] == [
        (1, "case-0"),
        (1, "case-1"),
        (2, "case-0"),
        (2, "case-1"),
        (3, "case-0"),
        (3, "case-1"),
    ]


def test_plan_calls_empty_for_no_cases() -> None:
    assert plan_calls([]) == []


def test_fixture_is_a_real_claude_json_result() -> None:
    data = json.loads(FIXTURE.read_text())
    assert data["type"] == "result"
    assert data["is_error"] is False
    assert data["usage"]["output_tokens"] > 0
    assert data["result"].lstrip("`\n").startswith("verdict:")


def test_call_returns_parsed_output_for_fixture_reply(
    source: tuple[Path, str], tmp_path: Path
) -> None:
    repo, revision = source
    case, folder = make_case(tmp_path, revision)
    run = Recording(FIXTURE.read_text())
    result = review_call(case, 1, "haiku", run, case_dir=folder, source_repo=repo)
    assert result.incomplete_reason is None
    assert result.parsed is not None
    assert result.parsed["verdict"] == "PASS"


def test_call_invokes_claude_print_with_model_json_and_reviewer_agent(
    source: tuple[Path, str], tmp_path: Path
) -> None:
    repo, revision = source
    case, folder = make_case(tmp_path, revision)
    run = Recording(envelope(REVIEW_TEXT))
    review_call(case, 1, "haiku", run, case_dir=folder, source_repo=repo)
    (argv,) = run.claude_calls()
    assert argv[0] == "claude"
    assert "--print" in argv
    assert argv[argv.index("--model") + 1] == "haiku"
    assert argv[argv.index("--output-format") + 1] == "json"
    assert argv[argv.index("--agent") + 1] == "reviewer"
    agents = json.loads(argv[argv.index("--agents") + 1])
    body = (REPO_ROOT / "agents" / "reviewer.md").read_text().split("---\n", 2)[2].strip()
    assert agents["reviewer"]["prompt"] == body
    assert agents["reviewer"]["tools"] == ["Read", "Grep", "Glob", "Bash"]


def test_call_loads_no_project_settings_or_hooks(source: tuple[Path, str], tmp_path: Path) -> None:
    repo, revision = source
    case, folder = make_case(tmp_path, revision)
    run = Recording(envelope(REVIEW_TEXT))
    review_call(case, 1, "haiku", run, case_dir=folder, source_repo=repo)
    (argv,) = run.claude_calls()
    assert argv[argv.index("--setting-sources") + 1] == "user"


def test_call_env_sets_canon_readonly_and_keeps_environment(
    source: tuple[Path, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("EVAL_MARKER", "kept")
    repo, revision = source
    case, folder = make_case(tmp_path, revision)
    run = Recording(envelope(REVIEW_TEXT))
    review_call(case, 1, "haiku", run, case_dir=folder, source_repo=repo)
    env = run.envs[-1]
    assert env is not None
    assert env["CANON_READONLY"] == "1"
    assert env["EVAL_MARKER"] == "kept"
    assert "PATH" in env and os.environ["PATH"] == env["PATH"]


def test_brief_has_frozen_records_and_case_tree_diff_without_self_grades(
    source: tuple[Path, str], tmp_path: Path
) -> None:
    repo, revision = source
    case, folder = make_case(tmp_path, revision)
    run = Recording(envelope(REVIEW_TEXT))
    review_call(case, 1, "haiku", run, case_dir=folder, source_repo=repo)
    (brief,) = [i for i in run.inputs if i]
    assert isinstance(brief, str)
    assert "WORKITEM-BODY" in brief
    assert "ACCEPT-CRITERION" in brief
    assert "SELF-GRADE-SECRET" not in brief
    assert "+two" in brief


def test_brief_includes_defect_patch_in_case_tree_diff(
    source: tuple[Path, str], tmp_path: Path
) -> None:
    repo, revision = source
    case, folder = make_case(tmp_path, revision)
    patch = folder / "defect.patch"
    patch.write_text(
        "diff --git a/a.txt b/a.txt\n--- a/a.txt\n+++ b/a.txt\n@@ -1,2 +1,2 @@\n one\n-two\n+DEFECT\n"
    )
    seeded = Case(**{**case.__dict__, "kind": "synthetic-defect", "patch": patch})
    run = Recording(envelope(REVIEW_TEXT))
    review_call(seeded, 1, "haiku", run, case_dir=folder, source_repo=repo)
    (brief,) = [i for i in run.inputs if i]
    assert isinstance(brief, str)
    assert "+DEFECT" in brief


def test_call_runs_in_a_case_tree_checkout_not_the_source_repo(
    source: tuple[Path, str], tmp_path: Path
) -> None:
    repo, revision = source
    case, folder = make_case(tmp_path, revision)
    run = Recording(envelope(REVIEW_TEXT))
    review_call(case, 1, "haiku", run, case_dir=folder, source_repo=repo)
    cwds = run.cwds
    assert cwds and all(cwd != repo for cwd in cwds)


def test_same_case_gives_the_same_brief_on_every_call_index(
    source: tuple[Path, str], tmp_path: Path
) -> None:
    repo, revision = source
    case, folder = make_case(tmp_path, revision)
    run = Recording(envelope(REVIEW_TEXT), envelope(REVIEW_TEXT))
    review_call(case, 1, "haiku", run, case_dir=folder, source_repo=repo)
    review_call(case, 2, "haiku", run, case_dir=folder, source_repo=repo)
    briefs = [i for i in run.inputs if i]
    assert len(briefs) == 2 and briefs[0] == briefs[1]


def test_tokens_sum_input_cache_and_output(source: tuple[Path, str], tmp_path: Path) -> None:
    repo, revision = source
    case, folder = make_case(tmp_path, revision)
    run = Recording(envelope(REVIEW_TEXT))
    result = review_call(case, 1, "haiku", run, case_dir=folder, source_repo=repo)
    assert result.tokens == 10 + 200 + 3000 + 40


def test_tokens_of_fixture_reply(source: tuple[Path, str], tmp_path: Path) -> None:
    repo, revision = source
    case, folder = make_case(tmp_path, revision)
    run = Recording(FIXTURE.read_text())
    result = review_call(case, 1, "haiku", run, case_dir=folder, source_repo=repo)
    assert result.tokens == 6 + 7560 + 13481 + 1077


def test_unparsable_reviewer_text_is_incomplete_with_tokens_kept(
    source: tuple[Path, str], tmp_path: Path
) -> None:
    repo, revision = source
    case, folder = make_case(tmp_path, revision)
    run = Recording(envelope("I could not decide."))
    result = review_call(case, 1, "haiku", run, case_dir=folder, source_repo=repo)
    assert result == CallResult(None, 3250, "unparsable")


def test_non_json_stdout_is_unparsable(source: tuple[Path, str], tmp_path: Path) -> None:
    repo, revision = source
    case, folder = make_case(tmp_path, revision)
    run = Recording("not json at all")
    result = review_call(case, 1, "haiku", run, case_dir=folder, source_repo=repo)
    assert result.parsed is None
    assert result.incomplete_reason == "unparsable"


def test_usage_limit_error_is_incomplete_usage_limit(
    source: tuple[Path, str], tmp_path: Path
) -> None:
    repo, revision = source
    case, folder = make_case(tmp_path, revision)
    run = Recording(envelope("Claude usage limit reached. Resets at 5pm.", is_error=True))
    result = review_call(case, 1, "haiku", run, case_dir=folder, source_repo=repo)
    assert result.parsed is None
    assert result.incomplete_reason == "usage_limit"


def test_error_result_is_incomplete_failed(source: tuple[Path, str], tmp_path: Path) -> None:
    repo, revision = source
    case, folder = make_case(tmp_path, revision)
    run = Recording(envelope("API Error: 500", is_error=True))
    result = review_call(case, 1, "haiku", run, case_dir=folder, source_repo=repo)
    assert result.parsed is None
    assert result.incomplete_reason == "failed"


def test_run_that_cannot_start_is_incomplete_failed(
    source: tuple[Path, str], tmp_path: Path
) -> None:
    repo, revision = source
    case, folder = make_case(tmp_path, revision)
    run = Recording(OSError("no claude"))
    result = review_call(case, 1, "haiku", run, case_dir=folder, source_repo=repo)
    assert result == CallResult(None, 0, "failed")


def test_call_result_is_frozen() -> None:
    result = CallResult(None, 0, None)
    with pytest.raises(AttributeError):
        result.tokens = 1  # pyright: ignore[reportAttributeAccessIssue] -- frozen dataclass is the behavior under test
