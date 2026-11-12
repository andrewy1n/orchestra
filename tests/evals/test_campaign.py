from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, overload

import pytest

from evals.seeded_defects.__main__ import main
from evals.seeded_defects.claude_call import Claude
from orchestra.tools.testing import ScriptedRun

REVIEW_TEXT = (
    "verdict: NEEDS_WORK\n"
    "findings:\n"
    "  - task: t1\n"
    "    kind: behavior-bug\n"
    "    expected: a\n"
    "    observed: a.txt is wrong\n"
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
USAGE = {
    "input_tokens": 10,
    "cache_creation_input_tokens": 200,
    "cache_read_input_tokens": 3000,
    "output_tokens": 40,
}
TOKENS = 3250
RECORDS = [
    {"record_type": "work-item", "subject": "wi-1", "title": "Add two", "body": "BODY"},
    {"record_type": "acceptance", "subject": "wi-1", "criterion": "C", "body": ""},
]
PATCH = (
    "diff --git a/a.txt b/a.txt\n--- a/a.txt\n+++ b/a.txt\n@@ -1,2 +1,2 @@\n one\n-two\n+DEFECT\n"
)


def envelope(result: str, *, is_error: bool = False) -> str:
    return json.dumps({"type": "result", "is_error": is_error, "result": result, "usage": USAGE})


GOOD = envelope(REVIEW_TEXT)
LIMIT = envelope("Claude usage limit reached.", is_error=True)
FAILED = envelope("API Error: 500", is_error=True)
UNPARSABLE = envelope("I could not decide.")


class Recording(ScriptedRun):
    def __init__(self, *replies: str, default: str | None = None) -> None:
        super().__init__(Claude, {}, Claude.min_version)
        self.replies = list(replies)
        self.default = default

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
            if self.replies:
                reply = self.replies.pop(0)
            else:
                assert self.default is not None, "unexpected claude call"
                reply = self.default
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


def yes(message: str) -> bool:
    return True


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "source"
    (path / "agents").mkdir(parents=True)
    (path / "orchestra" / "conductor").mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "t@example.com")
    git(path, "config", "user.name", "t")
    (path / "a.txt").write_text("one\n")
    (path / "agents" / "reviewer.md").write_text("prompt v1\n")
    (path / "orchestra" / "conductor" / "reviewer.py").write_text("X = 1\n")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "base")
    (path / "a.txt").write_text("one\ntwo\n")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "landing")
    return path


def add_case(cases: Path, repo: Path, case_id: str, *, defect: bool = False) -> None:
    folder = cases / case_id
    folder.mkdir(parents=True)
    meta: dict[str, object] = {
        "phase": "p1",
        "revision": git(repo, "rev-parse", "HEAD"),
        "kind": "synthetic-defect" if defect else "control",
    }
    if defect:
        meta |= {"defect_type": "reverted-change", "expected_files": ["a.txt"]}
        (folder / "defect.patch").write_text(PATCH)
    (folder / "case.json").write_text(json.dumps(meta))
    (folder / "records.json").write_text(json.dumps(RECORDS))
    (folder / "baseline.json").write_text("{}")


@pytest.fixture
def cases(tmp_path: Path, repo: Path) -> Path:
    path = tmp_path / "cases"
    add_case(path, repo, "c1")
    add_case(path, repo, "c2", defect=True)
    add_case(path, repo, "c3")
    return path


def review(
    run: Recording,
    repo: Path,
    cases: Path,
    campaign: Path,
    *extra: str,
    model: str = "haiku",
) -> int:
    argv = [
        "review",
        "--model",
        model,
        "--cases-dir",
        str(cases),
        "--repo",
        str(repo),
        "--campaign-dir",
        str(campaign),
        *extra,
    ]
    return main(argv, run=run, confirm=yes)


def saved(campaign: Path) -> list[str]:
    folder = campaign / "calls"
    return sorted(p.name for p in folder.glob("*.json")) if folder.is_dir() else []


def read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def test_records_model_prompt_commit_case_set(repo: Path, cases: Path, tmp_path: Path) -> None:
    campaign = tmp_path / "camp"
    prompt_commit = git(repo, "log", "-1", "--format=%H", "--", "agents/reviewer.md")
    assert review(Recording(default=GOOD), repo, cases, campaign) == 0
    record = read(campaign / "campaign.json")
    assert record["model"] == "haiku"
    assert record["prompt_commit"] == prompt_commit
    case_set_hash = record["case_set_hash"]
    assert isinstance(case_set_hash, str) and case_set_hash


def test_records_case_set_hash_changes_with_a_frozen_record(
    repo: Path, cases: Path, tmp_path: Path
) -> None:
    first, second = tmp_path / "one", tmp_path / "two"
    review(Recording(default=GOOD), repo, cases, first)
    (cases / "c1" / "records.json").write_text(json.dumps([*RECORDS, RECORDS[0]]))
    review(Recording(default=GOOD), repo, cases, second)
    assert (
        read(first / "campaign.json")["case_set_hash"]
        != read(second / "campaign.json")["case_set_hash"]
    )


def test_prompt_commit_is_last_commit_touching_either_prompt_file(
    repo: Path, cases: Path, tmp_path: Path
) -> None:
    (repo / "orchestra" / "conductor" / "reviewer.py").write_text("X = 2\n")
    git(repo, "commit", "-qam", "change reviewer module")
    expected = git(repo, "rev-parse", "HEAD")
    campaign = tmp_path / "camp"
    review(Recording(default=GOOD), repo, cases, campaign)
    assert read(campaign / "campaign.json")["prompt_commit"] == expected


def test_saves_result_when_call_ends(repo: Path, cases: Path, tmp_path: Path) -> None:
    campaign = tmp_path / "camp"
    run = Recording(default=GOOD)
    assert review(run, repo, cases, campaign) == 0
    assert saved(campaign) == [f"c{n}-{i}.json" for n in (1, 2, 3) for i in (1, 2, 3)]
    result = read(campaign / "calls" / "c2-1.json")
    assert result["case_id"] == "c2"
    assert result["call_index"] == 1
    assert result["tokens"] == TOKENS
    assert result["incomplete_reason"] is None
    assert result["incomplete"] is False
    assert result["verdict_catch"] is True
    assert result["located_catch"] is True
    assert result["false_alarm"] is False


def test_saves_result_when_call_ends_before_next_call_starts(
    repo: Path, cases: Path, tmp_path: Path
) -> None:
    campaign = tmp_path / "camp"
    review(Recording(GOOD, GOOD, LIMIT), repo, cases, campaign)
    assert saved(campaign) == ["c1-1.json", "c2-1.json"]


def test_control_case_flags_false_alarm_in_saved_result(
    repo: Path, cases: Path, tmp_path: Path
) -> None:
    campaign = tmp_path / "camp"
    review(Recording(default=GOOD), repo, cases, campaign)
    result = read(campaign / "calls" / "c1-1.json")
    assert result["false_alarm"] is True
    assert result["verdict_catch"] is False


def test_failed_call_saves_nothing(repo: Path, cases: Path, tmp_path: Path) -> None:
    campaign = tmp_path / "camp"
    review(Recording(FAILED, default=GOOD), repo, cases, campaign)
    assert "c1-1.json" not in saved(campaign)
    assert "c2-1.json" in saved(campaign)


def test_usage_limit_stops_the_run_and_saves_nothing_for_it(
    repo: Path, cases: Path, tmp_path: Path
) -> None:
    campaign = tmp_path / "camp"
    run = Recording(GOOD, LIMIT, default=GOOD)
    assert review(run, repo, cases, campaign) != 0
    assert len(run.claude_calls()) == 2
    assert saved(campaign) == ["c1-1.json"]


def test_unparsable_call_is_saved_as_incomplete_and_not_retried(
    repo: Path, cases: Path, tmp_path: Path
) -> None:
    campaign = tmp_path / "camp"
    run = Recording(UNPARSABLE, default=GOOD)
    review(run, repo, cases, campaign)
    result = read(campaign / "calls" / "c1-1.json")
    assert result["incomplete"] is True
    assert result["incomplete_reason"] == "unparsable"
    assert result["tokens"] == TOKENS
    assert len(run.claude_calls()) == 9


def test_resume_makes_only_missing_calls(repo: Path, cases: Path, tmp_path: Path) -> None:
    campaign = tmp_path / "camp"
    review(Recording(GOOD, GOOD, LIMIT), repo, cases, campaign)
    before = (campaign / "calls" / "c1-1.json").read_text()
    run = Recording(default=GOOD)
    assert review(run, repo, cases, campaign) == 0
    assert len(run.claude_calls()) == 7
    assert (campaign / "calls" / "c1-1.json").read_text() == before
    assert len(saved(campaign)) == 9


def test_resume_of_a_finished_campaign_makes_no_calls(
    repo: Path, cases: Path, tmp_path: Path
) -> None:
    campaign = tmp_path / "camp"
    review(Recording(default=GOOD), repo, cases, campaign)
    assert len(saved(campaign)) == 9
    run = Recording()
    assert review(run, repo, cases, campaign) == 0
    assert run.claude_calls() == []


def test_resume_does_not_retry_a_saved_unparsable_call(
    repo: Path, cases: Path, tmp_path: Path
) -> None:
    campaign = tmp_path / "camp"
    review(Recording(UNPARSABLE, default=GOOD), repo, cases, campaign)
    assert "c1-1.json" in saved(campaign)
    run = Recording()
    review(run, repo, cases, campaign)
    assert run.claude_calls() == []


def test_resume_refused_on_changed_inputs_model(repo: Path, cases: Path, tmp_path: Path) -> None:
    campaign = tmp_path / "camp"
    review(Recording(GOOD, LIMIT), repo, cases, campaign)
    run = Recording(default=GOOD)
    assert review(run, repo, cases, campaign, model="sonnet") != 0
    assert run.claude_calls() == []


def test_resume_refused_on_changed_inputs_prompt_commit(
    repo: Path, cases: Path, tmp_path: Path
) -> None:
    campaign = tmp_path / "camp"
    review(Recording(GOOD, LIMIT), repo, cases, campaign)
    (repo / "agents" / "reviewer.md").write_text("prompt v2\n")
    git(repo, "commit", "-qam", "change prompt")
    run = Recording(default=GOOD)
    assert review(run, repo, cases, campaign) != 0
    assert run.claude_calls() == []


def test_resume_refused_on_changed_inputs_case_set(repo: Path, cases: Path, tmp_path: Path) -> None:
    campaign = tmp_path / "camp"
    review(Recording(GOOD, LIMIT), repo, cases, campaign)
    (cases / "c1" / "records.json").write_text(json.dumps([RECORDS[0]]))
    run = Recording(default=GOOD)
    assert review(run, repo, cases, campaign) != 0
    assert run.claude_calls() == []


def test_named_subset_makes_six_calls(repo: Path, cases: Path, tmp_path: Path) -> None:
    campaign = tmp_path / "camp"
    run = Recording(default=GOOD)
    assert review(run, repo, cases, campaign, "--cases", "c1", "c2") == 0
    assert len(run.claude_calls()) == 6
    assert saved(campaign) == [f"c{n}-{i}.json" for n in (1, 2) for i in (1, 2, 3)]


def test_invalid_case_set_stops_before_any_call(repo: Path, cases: Path, tmp_path: Path) -> None:
    (cases / "c2" / "defect.patch").unlink()
    campaign = tmp_path / "camp"
    run = Recording(default=GOOD)
    assert review(run, repo, cases, campaign) != 0
    assert run.claude_calls() == []
    assert saved(campaign) == []


@pytest.mark.parametrize("path", ["agents/reviewer.md", "orchestra/conductor/reviewer.py"])
def test_refused_when_reviewer_prompt_file_is_dirty(
    repo: Path, cases: Path, tmp_path: Path, path: str
) -> None:
    (repo / path).write_text("dirty\n")
    campaign = tmp_path / "camp"
    run = Recording(default=GOOD)
    assert review(run, repo, cases, campaign) != 0
    assert run.claude_calls() == []
    assert not (campaign / "campaign.json").exists()


def test_model_is_required(repo: Path, cases: Path, tmp_path: Path) -> None:
    argv = ["review", "--cases-dir", str(cases), "--repo", str(repo)]
    argv += ["--campaign-dir", str(tmp_path / "camp")]
    with pytest.raises(SystemExit) as exit_info:
        main(argv, run=Recording(default=GOOD), confirm=yes)
    assert exit_info.value.code == 2
