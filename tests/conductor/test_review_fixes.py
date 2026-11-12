from __future__ import annotations

from pathlib import Path

import pytest
from test_task_land import EVIDENCE, PHASE, _git, _world
from test_wave_end import _land
from test_wave_end import _world as _end_world

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject
from orchestra.conductor import land_task, task_close, wave
from orchestra.conductor.check import run_check


def _commit_in(tree: Path, name: str, text: str) -> None:
    (tree / name).write_text(text)
    _git(tree, "add", name)
    _git(tree, "commit", "-qm", f"edit {name}")


def _blocking(project: Project, scope: str) -> list[str]:
    return [
        r["id"]
        for r in project.list("score:continuity-question")
        if r["payload"].get("scope") == scope and r["payload"].get("blocking") is True
    ]


def test_r11_review_fix_closes_a_task_whose_requirements_are_verified_without_own_checks(
    tmp_path: Path,
) -> None:
    project, repo, tree = _world(tmp_path)
    acceptance = project.resolve("score:acceptance", "a")
    assert run_check(acceptance_id=acceptance["id"], cwd=tree, store_root=repo).exit_code == 0
    landed = land_task.LandedTask(
        "a", PHASE, "", "rev", "report", (), str(EVIDENCE["result"]), str(EVIDENCE["verdict"])
    )
    assert task_close.close(project, landed, frozenset({"R1"})).state == "done"


def test_r13_review_fix_start_conflict_opens_a_question_and_starts_nothing(
    tmp_path: Path,
) -> None:
    project, repo = _end_world(tmp_path, {"a": "true", "b": "true"})
    for slug in ("a", "b"):
        record = project.resolve("score:work-item", slug)
        project.update(record["id"], record_type="score:work-item", transition="withdrawn")
    for slug in ("c", "d"):
        wave_item: JsonObject = {
            "title": slug,
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": "ef",
            "executor": "inline",
        }
        project.create(
            record_type="score:work-item",
            subject=slug,
            payload=wave_item,
            body="## Description\n\nd\n\n## Approach\n\na",
        )
    _git(repo, "branch", "task/ph/c", "phase/ph")
    _git(repo, "worktree", "add", "-q", str(repo / ".worktrees" / "ph--c"), "task/ph/c")
    _commit_in(repo / ".worktrees" / "ph--c", "shared.txt", "from c\n")
    _commit_in(repo / ".worktrees" / PHASE, "shared.txt", "from phase\n")
    with pytest.raises(wave.WaveError, match=r"conflict"):
        wave.start(project, repo, PHASE)
    assert project.resolve("score:work-item", "c")["lifecycle_state"] == "planned"
    assert project.resolve("score:work-item", "d")["lifecycle_state"] == "planned"
    assert len(_blocking(project, "merge:c")) == 1


def test_r13_review_fix_end_reuses_the_open_question_on_a_rerun(tmp_path: Path) -> None:
    project, repo = _end_world(tmp_path, {"a": "true", "b": "true"})
    _land(project, repo, "a", "shared.txt", "from a\n")
    _land(project, repo, "b", "shared.txt", "from b\n")
    first = wave.end(project, repo, PHASE)
    second = wave.end(project, repo, PHASE)
    assert first.question_id
    assert len(_blocking(project, "merge:b")) == 1
    assert second.conflict == "b"
    assert second.question_id == first.question_id


def test_r13_review_fix_end_reports_a_merge_failure_that_is_not_a_conflict(
    tmp_path: Path,
) -> None:
    project, repo = _end_world(tmp_path, {"a": "true"})
    _land(project, repo, "a", "new.txt", "from a\n")
    (repo / ".worktrees" / PHASE / "new.txt").write_text("untracked\n")
    with pytest.raises(wave.WaveError, match="git merge"):
        wave.end(project, repo, PHASE)
    assert _blocking(project, "merge:a") == []


def test_r14_review_fix_a_stale_pass_is_not_merged(tmp_path: Path) -> None:
    project, repo = _end_world(tmp_path, {"a": "true"})
    _land(project, repo, "a", "a.txt", "a\n")
    _commit_in(repo / ".worktrees" / f"{PHASE}--a", "later.txt", "later\n")
    result = wave.end(project, repo, PHASE)
    assert result.merged == ()
    assert result.skipped == (("a", "checks did not pass"),)
    assert result.conflict == ""
