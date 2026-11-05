from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from canon_support import create, make_project
from test_task_land import EVIDENCE, PHASE, _evidence_file, _git, _land_cli, _world
from test_wave_end import _world as _end_world

from orchestra.conductor import land_task, wave
from orchestra.conductor.check import run_check

NO_LANDING_BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n"


def _set_acceptance(project, **payload: object) -> None:
    record = project.resolve("score:acceptance", "a")
    project.update(record["id"], record_type="score:acceptance", payload=payload)


def test_pass_only_tdd_acceptance_does_not_close_the_task(tmp_path: Path) -> None:
    project, repo, _ = _world(tmp_path)
    _set_acceptance(project, method="tdd")
    result = _land_cli(repo, _evidence_file(tmp_path))
    assert result.returncode == 1
    out = json.loads(result.stdout)
    assert out["state"] == "in_progress"
    assert any("red_check_run_id" in reason for reason in out["reasons"])
    assert project.resolve("score:work-item", "a")["lifecycle_state"] == "in_progress"


def test_tdd_acceptance_without_an_oracle_freeze_does_not_close_even_after_a_red_run(
    tmp_path: Path,
) -> None:
    project, repo, tree = _world(tmp_path, verify_command="false")
    _set_acceptance(project, method="tdd")
    acceptance = project.resolve("score:acceptance", "a")
    assert run_check(acceptance_id=acceptance["id"], cwd=tree, store_root=repo).exit_code != 0
    time.sleep(1.1)
    _set_acceptance(project, verify_command="true")
    result = _land_cli(repo, _evidence_file(tmp_path))
    assert result.returncode == 1
    out = json.loads(result.stdout)
    assert out["state"] == "in_progress"
    assert any("oracle freeze" in reason for reason in out["reasons"])


def test_tdd_acceptance_with_a_drifted_oracle_hash_does_not_close_the_task(tmp_path: Path) -> None:
    project, repo, tree = _world(tmp_path, verify_command="false")
    (tree / "oracle.py").write_text("x = 1\n")
    _set_acceptance(
        project,
        method="tdd",
        test_ids=["oracle.py::test_x"],
        oracle_hashes=["oracle.py:sha256:" + "0" * 64],
    )
    acceptance = project.resolve("score:acceptance", "a")
    run_check(acceptance_id=acceptance["id"], cwd=tree, store_root=repo, allow_dirty=True)
    _set_acceptance(project, verify_command="true")
    result = _land_cli(repo, _evidence_file(tmp_path))
    assert result.returncode == 1
    assert json.loads(result.stdout)["state"] == "in_progress"


def test_needs_human_evidence_stops_the_close_and_opens_a_blocking_question(
    tmp_path: Path,
) -> None:
    project, repo, _ = _world(tmp_path)
    evidence = _evidence_file(tmp_path, verdict="inconclusive", needs_human=True)
    result = _land_cli(repo, evidence)
    assert result.returncode == 3
    out = json.loads(result.stdout)
    assert out["state"] == "in_progress"
    assert out["question"]
    question = project.get(out["question"], "score:continuity-question")
    assert question["payload"]["scope"] == "human:a"


def test_a_non_pass_verdict_does_not_close_the_task(tmp_path: Path) -> None:
    project, repo, _ = _world(tmp_path)
    result = _land_cli(repo, _evidence_file(tmp_path, verdict="delta"))
    assert result.returncode == 1
    assert project.resolve("score:work-item", "a")["lifecycle_state"] == "in_progress"


def test_manual_acceptance_exits_as_pending_human_action(tmp_path: Path) -> None:
    project, repo, _ = _world(tmp_path)
    _set_acceptance(project, method="manual")
    result = _land_cli(repo, _evidence_file(tmp_path))
    assert result.returncode == 3
    assert json.loads(result.stdout)["state"] == "in_progress"


def test_check_runner_receives_the_selected_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, repo, _ = _world(tmp_path)
    seen: dict[str, object] = {}
    real = land_task.run_check

    def spy(**kwargs: object):
        seen.update(kwargs)
        return real(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(land_task, "run_check", spy)
    land_task.land(project, repo, "a", _evidence_file(tmp_path))
    assert seen["store_dir"] == project.store_path


def test_staged_canon_changes_refuse_the_task_commit(tmp_path: Path) -> None:
    project, repo, tree = _world(tmp_path)
    (tree / ".canon").mkdir(exist_ok=True)
    (tree / ".canon" / "extra.json").write_text("{}\n")
    (tree / "work.txt").write_text("work\n")
    _git(tree, "add", "-f", ".canon/extra.json")
    with pytest.raises(land_task.LandError, match=r"staged \.canon"):
        land_task.land(project, repo, "a", _evidence_file(tmp_path))
    assert _git(tree, "log", "--format=%s", "-1") == "base"


def test_unstaged_canon_changes_stay_out_of_the_task_commit(tmp_path: Path) -> None:
    project, repo, tree = _world(tmp_path)
    (tree / ".canon").mkdir(exist_ok=True)
    (tree / ".canon" / "extra.json").write_text("{}\n")
    (tree / "work.txt").write_text("work\n")
    land_task.land(project, repo, "a", _evidence_file(tmp_path))
    files = _git(tree, "show", "--name-only", "--format=", "HEAD").splitlines()
    assert files == ["work.txt"]


def test_evidence_for_another_revision_is_refused(tmp_path: Path) -> None:
    project, repo, tree = _world(tmp_path)
    (tree / "work.txt").write_text("work\n")
    with pytest.raises(land_task.LandError, match="evidence revision"):
        land_task.land(project, repo, "a", _evidence_file(tmp_path, revision="0" * 40))
    assert _git(tree, "log", "--format=%s", "-1") == "base"


def test_evidence_for_the_current_head_lands(tmp_path: Path) -> None:
    project, repo, tree = _world(tmp_path)
    head = _git(tree, "rev-parse", "HEAD")
    landed = land_task.land(project, repo, "a", _evidence_file(tmp_path, revision=head))
    assert landed.task == EVIDENCE["subject"]


def test_non_landing_phase_works_in_the_caller_worktree(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "base.txt").write_text("base\n")
    _git(tmp_path, "add", "base.txt")
    _git(tmp_path, "commit", "-qm", "base")
    _git(tmp_path, "branch", "-M", "main")
    create(project, "score:effort", "ef", {"goal": "g", "kind": "deliver"})
    create(
        project,
        "score:phase",
        "ph",
        {"title": "Ph", "ordinal": 1, "effort": "ef"},
        NO_LANDING_BODY,
    )
    create(
        project,
        "score:work-item",
        "a",
        {
            "title": "a",
            "phase": "ph",
            "kind": "deliver",
            "assignee": "",
            "effort": "ef",
            "executor": "inline",
        },
        "## Description\n\nd\n\n## Approach\n\na",
    )
    linked = tmp_path / ".worktrees" / "feature"
    _git(tmp_path, "worktree", "add", "-q", "-b", "feature", str(linked))
    assert wave.worktree_root(linked) == linked
    assert wave.repo_root(linked) == tmp_path
    started = wave.start(project, wave.repo_root(linked), "ph", wave.worktree_root(linked))
    assert started.tasks[0].write_root == str(linked)


def test_wave_end_skips_a_task_that_is_not_closed(tmp_path: Path) -> None:
    project, repo = _end_world(tmp_path, {"a": "true"})
    (repo / ".worktrees" / f"{PHASE}--a" / "a.txt").write_text("a\n")
    evidence = repo / "a.json"
    evidence.write_text(json.dumps({**EVIDENCE, "evidence": "e"}))
    land_task.land(project, repo, "a", evidence)
    result = wave.end(project, repo, PHASE)
    assert result.merged == ()
    assert result.skipped == (("a", "task is not closed"),)
