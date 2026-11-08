from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest
from canon_support import create, make_project, seed_effort

from orchestra.canon.project import Project
from orchestra.conductor import close

PHASE = "p1"
URL = "https://github.com/o/r/pull/7"


@dataclass
class FakeStates:
    state: str
    head_sha: str
    calls: int = 0

    def pull_request_state(self, number: int) -> tuple[str, str]:
        assert number == 7
        self.calls += 1
        return self.state, self.head_sha


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _commit(root: Path, name: str) -> str:
    (root / name).write_text(name, encoding="utf-8")
    _git(root, "add", name)
    _git(root, "commit", "-qm", name)
    return _git(root, "rev-parse", "HEAD")


@dataclass
class Landed:
    project: Project
    repo: Path
    head: str

    @property
    def phase_tree(self) -> Path:
        return self.repo / ".worktrees" / PHASE

    @property
    def task_tree(self) -> Path:
        return self.repo / ".worktrees" / f"{PHASE}--a"

    def states(self, state: str = "MERGED", head: str | None = None) -> FakeStates:
        return FakeStates(state, head or self.head)

    def close(self, states: FakeStates) -> close.CloseResult:
        return close.close_phase(self.project, self.repo, PHASE, states)


def make_landed(tmp_path: Path, *, shared_repo: bool = False) -> Landed:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    _commit(repo, "base.txt")
    _git(repo, "branch", f"phase/{PHASE}")
    _git(repo, "worktree", "add", "-q", str(repo / ".worktrees" / PHASE), f"phase/{PHASE}")
    head = _commit(repo / ".worktrees" / PHASE, "work.txt")
    _git(repo, "branch", f"task/{PHASE}/a", f"phase/{PHASE}")
    _git(
        repo,
        "worktree",
        "add",
        "-q",
        str(repo / ".worktrees" / f"{PHASE}--a"),
        f"task/{PHASE}/a",
    )
    project = make_project(repo if shared_repo else tmp_path / "store")
    seed_effort(project, "alpha", PHASE)
    create(
        project,
        "conductor:landing",
        PHASE,
        {
            "phase": PHASE,
            "effort": "alpha",
            "number": 7,
            "url": URL,
            "head_sha": head,
            "result": "success",
        },
    )
    return Landed(project, repo, head)


@pytest.fixture
def landed(tmp_path: Path) -> Landed:
    return make_landed(tmp_path)


def test_close_acts_only_on_merged(landed: Landed) -> None:
    for state in ("OPEN", "CLOSED"):
        result = landed.close(landed.states(state))
        assert not result.ready
        assert result.refusals == ()

    merged = landed.close(landed.states("MERGED"))

    assert merged.ready
    assert merged.state == "MERGED"
    assert merged.number == 7


def test_close_open_pr_changes_nothing(landed: Landed) -> None:
    before = _git(landed.repo, "branch", "--list")
    phase = landed.project.resolve("score:phase", PHASE)

    states = landed.states("OPEN")

    landed.close(states)

    assert states.calls == 1
    assert landed.phase_tree.is_dir()
    assert landed.task_tree.is_dir()
    assert _git(landed.repo, "branch", "--list") == before
    assert landed.project.resolve("score:phase", PHASE)["revision"] == phase["revision"]


def test_close_reports_pull_request_state(landed: Landed) -> None:
    result = landed.close(landed.states("OPEN"))

    assert result.state == "OPEN"
    assert "OPEN" in result.message
    assert "7" in result.message


def test_close_refuses_dirty_worktree(landed: Landed) -> None:
    (landed.task_tree / "scratch.txt").write_text("x", encoding="utf-8")

    result = landed.close(landed.states())

    assert not result.ready
    assert any("uncommitted" in line for line in result.refusals)


def test_close_refuses_phase_branch_tip_mismatch(landed: Landed) -> None:
    _commit(landed.phase_tree, "late.txt")

    result = landed.close(landed.states())

    assert not result.ready
    assert any(f"phase/{PHASE}" in line and "differs" in line for line in result.refusals)


def test_close_refusal_names_path_or_branch(landed: Landed) -> None:
    (landed.phase_tree / "scratch.txt").write_text("x", encoding="utf-8")
    _commit(landed.task_tree, "extra.txt")

    result = landed.close(landed.states())

    text = "\n".join(result.refusals)
    assert str(landed.phase_tree) in text
    assert f"task/{PHASE}/a" in text


def test_close_refuses_task_branch_not_in_phase(landed: Landed) -> None:
    _commit(landed.task_tree, "extra.txt")

    result = landed.close(landed.states())

    assert not result.ready
    assert any(f"task/{PHASE}/a" in line and "not in" in line for line in result.refusals)


def test_close_needs_a_landing_record(tmp_path: Path) -> None:
    project = make_project(tmp_path / "store")
    seed_effort(project, "alpha", PHASE)

    with pytest.raises(close.CloseError, match="landing"):
        close.close_phase(project, tmp_path, PHASE, FakeStates("MERGED", "a" * 40))


def test_close_cli_reports_the_pull_request_state(
    landed: Landed, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from orchestra.cli import main

    monkeypatch.setattr(close, "github_states", lambda _repo: landed.states("OPEN"))

    code = main(
        [
            "close",
            "--phase",
            PHASE,
            "--cwd",
            str(landed.repo),
            "--store",
            str(landed.project.project_root),
        ]
    )

    assert code == 0
    output = capsys.readouterr().out
    assert '"state": "OPEN"' in output
    assert '"ready": false' in output


def test_close_cli_exits_one_when_a_refusal_stands(
    landed: Landed, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from orchestra.cli import main

    (landed.task_tree / "scratch.txt").write_text("x", encoding="utf-8")
    monkeypatch.setattr(close, "github_states", lambda _repo: landed.states("MERGED"))

    code = main(
        [
            "close",
            "--phase",
            PHASE,
            "--cwd",
            str(landed.repo),
            "--store",
            str(landed.project.project_root),
        ]
    )

    assert code == 1
    assert str(landed.task_tree) in capsys.readouterr().err


def test_close_refuses_a_worktree_holding_the_current_directory(landed: Landed) -> None:
    inside = landed.phase_tree / "nested"
    inside.mkdir()

    result = close.close_phase(landed.project, landed.repo, PHASE, landed.states(), cwd=inside)

    assert not result.ready
    assert any(
        str(landed.phase_tree) in line and "current directory" in line for line in result.refusals
    )
    assert landed.phase_tree.is_dir()
    assert _git(landed.repo, "branch", "--list", f"phase/{PHASE}") != ""


def test_close_from_the_main_checkout_still_closes(landed: Landed) -> None:
    result = close.close_phase(landed.project, landed.repo, PHASE, landed.states(), cwd=landed.repo)

    assert result.ready
    assert not landed.phase_tree.exists()


def test_close_help_says_what_close_does(capsys: pytest.CaptureFixture[str]) -> None:
    from orchestra.cli import main

    with pytest.raises(SystemExit):
        main(["close", "--help"])

    out = " ".join(capsys.readouterr().out.split())
    assert "removes the worktrees and branches" in out
    assert "After the pull request merges" in out
