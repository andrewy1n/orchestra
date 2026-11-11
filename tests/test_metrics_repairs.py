from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from canon_support import create, make_project, seed_effort

from orchestra.canon.project import Project
from orchestra.cli import main
from orchestra.metrics.repairs import RepairRow, build_repair_rows


def _git(root: Path, *args: str, date: str | None = None) -> str:
    env = dict(os.environ)
    if date:
        env["GIT_AUTHOR_DATE"] = date
        env["GIT_COMMITTER_DATE"] = date
    result = subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return result.stdout.strip()


def _commit(root: Path, subject: str, date: str) -> str:
    _git(root, "commit", "--allow-empty", "-q", "-m", subject, date=date)
    return _git(root, "rev-parse", "HEAD")


def _link(project: Project, sha: str, cause: str, phase: str | None = None) -> None:
    payload: dict = {"fix": sha, "cause": cause}
    if phase is not None:
        payload["phase"] = phase
    create(project, "conductor:repair-link", f"link-{sha[:8]}", payload)


@pytest.fixture
def project(tmp_path: Path) -> Project:
    project = make_project(tmp_path)
    seed_effort(project)
    _git(tmp_path, "checkout", "-q", "-b", "main")
    _commit(tmp_path, "chore: start", "2026-10-01T00:00:00+00:00")
    return project


def _cli(root: Path, *extra: str) -> int:
    return main(["metrics", "repairs", "--since", "2026-10-26", *extra, str(root)])


def test_lists_each_fix_commit_with_its_link(tmp_path: Path, project: Project) -> None:
    linked = _commit(tmp_path, "fix: repair x", "2026-10-27T00:00:00+00:00")
    marked = _commit(tmp_path, "fix(cli): repair y", "2026-10-28T00:00:00+00:00")
    _commit(tmp_path, "feat: not a fix", "2026-10-29T00:00:00+00:00")
    _link(project, linked, "spec-gap", "p1")
    _link(project, marked, "no-phase")

    rows = {r.sha: r for r in build_repair_rows(tmp_path, since="2026-10-26")}

    assert set(rows) == {linked, marked}
    assert isinstance(rows[linked], RepairRow)
    assert rows[linked].subject == "fix: repair x"
    assert (rows[linked].cause, rows[linked].phase) == ("spec-gap", "p1")
    assert (rows[marked].cause, rows[marked].phase) == ("no-phase", None)


def test_cli_prints_each_fix_with_its_link(
    tmp_path: Path, project: Project, capsys: pytest.CaptureFixture[str]
) -> None:
    linked = _commit(tmp_path, "fix: repair x", "2026-10-27T00:00:00+00:00")
    _link(project, linked, "verification-miss", "p1")

    code = _cli(tmp_path)

    out = capsys.readouterr().out
    assert code == 0
    assert linked in out
    assert "fix: repair x" in out
    assert "verification-miss" in out
    assert "p1" in out


def test_exit_1_when_a_fix_commit_has_no_link(
    tmp_path: Path, project: Project, capsys: pytest.CaptureFixture[str]
) -> None:
    linked = _commit(tmp_path, "fix: repair x", "2026-10-27T00:00:00+00:00")
    bare = _commit(tmp_path, "fix: repair z", "2026-10-28T00:00:00+00:00")
    _link(project, linked, "spec-gap", "p1")

    code = _cli(tmp_path)

    out = capsys.readouterr().out
    assert code == 1
    assert bare in out
    assert "fix: repair z" in out


def test_exit_0_when_all_fixes_are_linked_or_marked_no_phase(
    tmp_path: Path, project: Project
) -> None:
    linked = _commit(tmp_path, "fix: repair x", "2026-10-27T00:00:00+00:00")
    marked = _commit(tmp_path, "fix: repair y", "2026-10-28T00:00:00+00:00")
    _link(project, linked, "requirement-change", "p1")
    _link(project, marked, "no-phase")

    assert _cli(tmp_path) == 0


def test_exit_0_when_no_fix_commit_is_in_the_window(tmp_path: Path, project: Project) -> None:
    _commit(tmp_path, "feat: add", "2026-10-27T00:00:00+00:00")

    assert _cli(tmp_path) == 0


def test_since_excludes_older_fix_commits(
    tmp_path: Path, project: Project, capsys: pytest.CaptureFixture[str]
) -> None:
    old = _commit(tmp_path, "fix: old repair", "2026-10-10T00:00:00+00:00")
    new = _commit(tmp_path, "fix: new repair", "2026-10-30T00:00:00+00:00")
    _link(project, new, "spec-gap", "p1")

    code = _cli(tmp_path)

    out = capsys.readouterr().out
    assert code == 0
    assert old not in out
    assert new in out
    assert [r.sha for r in build_repair_rows(tmp_path, since="2026-10-26")] == [new]
    assert {r.sha for r in build_repair_rows(tmp_path, since="2026-10-01")} == {old, new}


def test_reads_main_not_the_checked_out_branch(tmp_path: Path, project: Project) -> None:
    on_main = _commit(tmp_path, "fix: on main", "2026-10-27T00:00:00+00:00")
    _git(tmp_path, "checkout", "-q", "-b", "side")
    _commit(tmp_path, "fix: on side", "2026-10-28T00:00:00+00:00")

    assert [r.sha for r in build_repair_rows(tmp_path, since="2026-10-26")] == [on_main]


def test_command_leaves_the_store_unchanged(tmp_path: Path, project: Project) -> None:
    sha = _commit(tmp_path, "fix: repair x", "2026-10-27T00:00:00+00:00")
    _link(project, sha, "spec-gap", "p1")
    before = len(project.records())

    _cli(tmp_path)

    assert len(project.records()) == before
