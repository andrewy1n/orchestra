from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from canon_support import REPO
from test_wave_end import PHASE, _git, _land, _world

from orchestra.canon.project import Project
from orchestra.conductor import wave


def _conflict(tmp_path: Path) -> tuple[Project, Path, Path]:
    project, repo = _world(tmp_path, {"a": "true", "b": "true"})
    _land(project, repo, "a", "shared.txt", "from a\n")
    _land(project, repo, "b", "shared.txt", "from b\n")
    result = wave.end(project, repo, PHASE)
    assert result.conflict == "b"
    return project, repo, repo / ".worktrees" / PHASE


def _open_questions(project: Project) -> list[str]:
    return [
        str(record["payload"].get("scope"))
        for record in project.list("score:continuity-question")
        if record["lifecycle_state"] == "open"
    ]


def test_resolve_refuses_while_an_unmerged_path_remains(tmp_path: Path) -> None:
    project, repo, _tree = _conflict(tmp_path)
    result = wave.resolve(project, repo, PHASE, "b")
    assert not result.ready
    assert any("unmerged" in reason and "shared.txt" in reason for reason in result.refusals)


def test_resolve_refuses_while_a_conflict_marker_remains(tmp_path: Path) -> None:
    project, repo, tree = _conflict(tmp_path)
    _git(tree, "add", "shared.txt")
    result = wave.resolve(project, repo, PHASE, "b")
    assert not result.ready
    assert not any("unmerged" in reason for reason in result.refusals)
    assert any("conflict marker" in reason and "shared.txt" in reason for reason in result.refusals)


def test_resolve_marker_check_ignores_unchanged_files_that_hold_marker_text(
    tmp_path: Path,
) -> None:
    project, repo, tree = _conflict(tmp_path)
    (tree / "shared.txt").write_text("from a\nfrom b\n")
    _git(tree, "add", "shared.txt")
    result = wave.resolve(project, repo, PHASE, "b")
    assert result.ready, result.refusals


def test_resolve_refused_leaves_the_question_open_and_writes_no_record(tmp_path: Path) -> None:
    project, repo, tree = _conflict(tmp_path)
    before = len(project.records())
    head = _git(tree, "rev-parse", "HEAD")
    result = wave.resolve(project, repo, PHASE, "b")
    assert not result.ready
    assert "merge:b" in _open_questions(project)
    assert len(project.records()) == before
    assert _git(tree, "rev-parse", "HEAD") == head


def test_resolve_question_open_is_required(tmp_path: Path) -> None:
    project, repo = _world(tmp_path, {"a": "true"})
    result = wave.resolve(project, repo, PHASE, "a")
    assert not result.ready
    assert any("merge:a" in reason for reason in result.refusals)


def _grep_world(tmp_path: Path, extra: tuple[str, ...] = ()) -> tuple[Project, Path, Path]:
    commands = {"a": "grep -q 'from a' shared.txt", "b": "grep -q 'from b' shared.txt"}
    commands.update({slug: "true" for slug in extra})
    project, repo = _world(tmp_path, commands)
    _land(project, repo, "a", "shared.txt", "from a\n")
    _land(project, repo, "b", "shared.txt", "from b\n")
    for slug in extra:
        _land(project, repo, slug, f"{slug}.txt", f"{slug}\n")
    result = wave.end(project, repo, PHASE)
    assert result.conflict == "b"
    return project, repo, repo / ".worktrees" / PHASE


def _keep(tree: Path, text: str) -> None:
    (tree / "shared.txt").write_text(text)
    _git(tree, "add", "shared.txt")


def test_resolve_incoming_acceptance_must_pass_on_the_merge(tmp_path: Path) -> None:
    project, repo, tree = _grep_world(tmp_path)
    _keep(tree, "from a\n")
    result = wave.resolve(project, repo, PHASE, "b")
    assert not result.ready
    assert any("acceptance failed" in reason and "b" in reason for reason in result.refusals)
    assert "merge:b" in _open_questions(project)


def test_resolve_merged_acceptance_must_pass_on_the_merge(tmp_path: Path) -> None:
    project, repo, tree = _grep_world(tmp_path)
    _keep(tree, "from b\n")
    result = wave.resolve(project, repo, PHASE, "b")
    assert not result.ready
    assert any("acceptance failed" in reason and "a" in reason for reason in result.refusals)
    assert "merge:b" in _open_questions(project)


def test_resolve_commits_merge_with_both_parents(tmp_path: Path) -> None:
    project, repo, tree = _grep_world(tmp_path)
    before = _git(tree, "rev-parse", "HEAD")
    _keep(tree, "from a\nfrom b\n")
    result = wave.resolve(project, repo, PHASE, "b")
    assert result.ready, result.refusals
    head = _git(tree, "rev-parse", "HEAD")
    assert head == result.commit
    parents = _git(tree, "rev-list", "--parents", "-n", "1", "HEAD").split()[1:]
    assert parents[0] == before
    assert parents[1] == _git(repo, "rev-parse", f"task/{PHASE}/b")
    assert _git(tree, "status", "--porcelain") == ""
    assert not (Path(_git(tree, "rev-parse", "--git-dir")) / "MERGE_HEAD").exists()
    assert (tree / "shared.txt").read_text() == "from a\nfrom b\n"
    assert not (repo / ".worktrees" / f"{PHASE}--resolve-b").exists()


def test_resolve_records_check_runs_at_the_merge_commit(tmp_path: Path) -> None:
    project, repo, tree = _grep_world(tmp_path)
    _keep(tree, "from a\nfrom b\n")
    result = wave.resolve(project, repo, PHASE, "b")
    assert result.ready, result.refusals
    at_merge = {
        record["subject"]
        for record in project.list("tuner:check-run")
        if record["payload"].get("revision") == result.commit
        and record["payload"].get("result") == "pass"
    }
    assert {"a", "b"} <= at_merge


def test_resolve_answers_question_for_the_merge(tmp_path: Path) -> None:
    project, repo, tree = _grep_world(tmp_path)
    _keep(tree, "from a\nfrom b\n")
    assert wave.resolve(project, repo, PHASE, "b").ready
    assert "merge:b" not in _open_questions(project)
    answered = [
        record
        for record in project.list("score:continuity-question")
        if record["payload"].get("scope") == "merge:b"
    ]
    assert [record["lifecycle_state"] for record in answered] == ["answered"]


def test_resolve_wave_end_continues_with_the_remaining_tasks(tmp_path: Path) -> None:
    project, repo, tree = _grep_world(tmp_path, extra=("c",))
    assert not (tree / "c.txt").exists()
    _keep(tree, "from a\nfrom b\n")
    assert wave.resolve(project, repo, PHASE, "b").ready
    result = wave.end(project, repo, PHASE)
    assert result.conflict == ""
    assert result.merged == ("c",)
    assert (tree / "c.txt").exists()


def test_resolve_cli_exits_one_and_names_the_reason_while_a_conflict_remains(
    tmp_path: Path,
) -> None:
    _project, repo, _tree = _conflict(tmp_path)
    env = dict(os.environ, PYTHONPATH=str(REPO))
    result = subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "wave", "resolve", PHASE, "b"],
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
    )
    assert result.returncode == 1
    assert "shared.txt" in result.stderr
    payload = subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "wave", "resolve", PHASE, "b", "--json"],
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
    )
    assert payload.returncode == 1
    assert json.loads(payload.stdout)["ready"] is False


def _cli(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(REPO))
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "wave", *args],
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
    )


def test_end_to_end_wave_resolve(tmp_path: Path) -> None:
    project, repo = _world(
        tmp_path,
        {"a": "grep -q 'from a' shared.txt", "b": "grep -q 'from b' shared.txt"},
    )
    _land(project, repo, "a", "shared.txt", "from a\n")
    _land(project, repo, "b", "shared.txt", "from b\n")
    tree = repo / ".worktrees" / PHASE

    ended = _cli(repo, "end", PHASE)
    assert ended.returncode == 1
    assert "merge:b" in _open_questions(project)

    refused = _cli(repo, "resolve", PHASE, "b")
    assert refused.returncode == 1
    assert "unmerged" in refused.stderr

    _keep_both(tree)
    resolved = _cli(repo, "resolve", PHASE, "b")
    assert resolved.returncode == 0, resolved.stderr
    assert "merge:b" not in _open_questions(project)
    assert _git(tree, "status", "--porcelain") == ""


def _keep_both(tree: Path) -> None:
    (tree / "shared.txt").write_text("from a\nfrom b\n")
    _git(tree, "add", "shared.txt")
