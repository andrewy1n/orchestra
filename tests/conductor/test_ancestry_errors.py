from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from canon_support import create, make_project
from conductor_support import PHASE as GATE_PHASE
from conductor_support import Cli, seed
from conftest import REPO_ROOT, git
from test_close_batch import RUNNER, _ancestry_repo, _build, _request

from orchestra.canon.project import Project
from orchestra.conductor import close_batch, wave
from orchestra.tools import Git
from orchestra.tuner.manifest import Claim, Manifest
from orchestra.tuner.provenance import AFTER, check_provenance

UNKNOWN = "f" * 40
PHASE = "ancestry-phase"
EFFORT = "ancestry-effort"
PHASE_BODY = (
    "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n\n"
    f"## Landing\n\nbranch: phase/{PHASE}\nworktree: <repo>/.worktrees/{PHASE}\nbase: main\n"
)
GIT_FAILURE = re.compile(r"not a valid (object name|commit name)|unknown revision", re.IGNORECASE)


def test_ancestry_checks_use_is_ancestor() -> None:
    source = REPO_ROOT / "orchestra"
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in source.rglob("*.py")
        if path != source / "tools" / "git.py" and "--is-ancestor" in path.read_text()
    ]
    assert offenders == []


def _world(tmp_path: Path) -> tuple[Project, Path]:
    project = make_project(tmp_path)
    repo = Git(tmp_path)
    repo.run("config", "user.email", "test@example.com")
    repo.run("config", "user.name", "test")
    (tmp_path / "base.txt").write_text("base\n")
    repo.run("add", "base.txt")
    repo.run("commit", "-qm", "base")
    repo.run("branch", "-M", "main")
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    create(
        project,
        "score:phase",
        PHASE,
        {"title": PHASE, "ordinal": 1, "effort": EFFORT},
        PHASE_BODY,
    )
    repo.run("branch", f"phase/{PHASE}", "main")
    (tmp_path / ".worktrees").mkdir()
    repo.run("worktree", "add", "-q", str(tmp_path / ".worktrees" / PHASE), f"phase/{PHASE}")
    return project, tmp_path


def _done_item(project: Project, slug: str) -> None:
    create(
        project,
        "score:work-item",
        slug,
        {
            "title": slug,
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "executor": "inline",
            "depends_on": [],
        },
        f"## Description\n\nDo {slug}.\n\n## Approach\n\nImplement {slug}.",
    )
    item = project.resolve("score:work-item", slug)
    project.update(item["id"], record_type="score:work-item", transition="in_progress")
    item = project.resolve("score:work-item", slug)
    project.update(item["id"], record_type="score:work-item", transition="done")


def _task_tree(repo: Path, slug: str) -> tuple[Path, str]:
    branch = f"task/{PHASE}/{slug}"
    tree = repo / ".worktrees" / f"{PHASE}--{slug}"
    Git(repo).create_branch(branch, f"phase/{PHASE}")
    Git(repo).add_worktree(tree, branch)
    return tree, branch


def _commit(tree: Path, name: str) -> None:
    (tree / name).write_text(name)
    git(tree, "add", name)
    git(tree, "commit", "-qm", name)


def _lose_phase_branch(repo: Path) -> None:
    git(repo, "branch", "-m", f"phase/{PHASE}", "phase/lost")


def _prepare(project: Project, repo: Path) -> tuple[Path, str]:
    item = project.resolve("score:work-item", "t")
    return wave._prepare(repo, PHASE, item, closing=False)


def test_wave_prepare_unknown_revision_raises_wave_error_naming_git(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    _done_item(project, "t")
    _task_tree(repo, "t")
    _lose_phase_branch(repo)
    with pytest.raises(wave.WaveError, match=GIT_FAILURE):
        _prepare(project, repo)


def test_wave_prepare_valid_negative_merges_the_phase_branch(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    _done_item(project, "t")
    tree, branch = _task_tree(repo, "t")
    _commit(repo / ".worktrees" / PHASE, "ahead.txt")
    result = _prepare(project, repo)
    assert result == (tree, branch)
    assert (tree / "ahead.txt").exists()


def test_wave_end_unknown_revision_raises_wave_error_naming_git(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    _done_item(project, "t")
    _task_tree(repo, "t")
    _lose_phase_branch(repo)
    with pytest.raises(wave.WaveError, match=GIT_FAILURE):
        wave.end(project, repo, PHASE)


def test_wave_end_valid_negative_skips_the_unchecked_task(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    _done_item(project, "t")
    tree, _ = _task_tree(repo, "t")
    _commit(tree, "task.txt")
    result = wave.end(project, repo, PHASE)
    assert result.merged == ()
    assert result.skipped == (("t", "checks did not pass"),)


def _gate_orchestra(store: Path) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in {"ORCHESTRA_STORE", "CANON_STORE"}}
    env["PYTHONPATH"] = os.pathsep.join(
        dict.fromkeys([str(REPO_ROOT), *filter(None, [env.get("PYTHONPATH")])])
    )
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "gate", GATE_PHASE, "--store", str(store)],
        capture_output=True,
        text=True,
        cwd=str(store),
        env=env,
    )


def _gate_world(store: Path, cli: Cli, reviewed: str = ""):
    phase = seed(store, cli, review=False, runner_check=False)
    worktree = phase.repo / ".worktrees" / GATE_PHASE
    git(phase.repo, "worktree", "add", "-q", str(worktree), "phase/x")
    if not reviewed:
        git(phase.repo, "checkout", "-q", "--detach", "main")
        git(phase.repo, "commit", "--allow-empty", "-qm", "side")
        reviewed = git(phase.repo, "rev-parse", "HEAD").stdout.strip()
        git(phase.repo, "checkout", "-q", "main")
    phase.review(revision=reviewed)
    return phase


def test_gate_unknown_revision_term_names_the_git_failure(store: Path, cli: Cli) -> None:
    phase = _gate_world(store, cli, UNKNOWN)
    term = phase.term("head-descends-from-review")
    assert not term.holds
    assert "does not descend" not in term.detail
    assert GIT_FAILURE.search(term.detail)
    result = _gate_orchestra(store)
    assert result.returncode == 1
    assert GIT_FAILURE.search(result.stdout)


def test_gate_valid_negative_keeps_the_does_not_descend_detail(store: Path, cli: Cli) -> None:
    phase = _gate_world(store, cli)
    term = phase.term("head-descends-from-review")
    assert not term.holds
    assert "does not descend from" in term.detail


def test_close_batch_unknown_revision_refuses_naming_git(tmp_path: Path) -> None:
    repo, _red, green = _ancestry_repo(tmp_path)
    entry = _red_first_entry(red=UNKNOWN, green=green)
    with pytest.raises(close_batch.CloseRefused, match=GIT_FAILURE):
        _build(_request(criteria=[entry]), cwd=repo)


def test_close_batch_valid_negative_keeps_the_not_a_descendant_refusal(tmp_path: Path) -> None:
    repo, red, green = _ancestry_repo(tmp_path)
    entry = _red_first_entry(red=green, green=red)
    with pytest.raises(close_batch.CloseRefused) as excinfo:
        _build(_request(criteria=[entry]), cwd=repo)
    assert str(excinfo.value) == (
        "criterion 'rec-ac1': green revision is not equal to or "
        f"a git descendant of red revision (red={green}, green={red})"
    )


def _red_first_entry(*, red: str, green: str) -> dict[str, object]:
    return {
        "criterion_id": "rec-ac1",
        "method": "tdd",
        "check_run_id": "rec-runner-green",
        "result": "pass",
        "revision": green,
        "red_check_run_id": "rec-runner-red",
        "red_result": "fail",
        "red_revision": red,
        "red_runner": RUNNER,
    }


ORACLE_REL = "tests/test_widget.py"


def _provenance_repo(root: Path) -> tuple[str, str, str]:
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "test@example.com")
    git(root, "config", "user.name", "test")
    (root / "app.py").write_text("value = 0\n")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "base")
    base = git(root, "rev-parse", "HEAD").stdout.strip()
    (root / "tests").mkdir()
    (root / ORACLE_REL).write_text("oracle\n")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "oracle")
    at = git(root, "rev-parse", "HEAD").stdout.strip()
    (root / "app.py").write_text("value = 1\n")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "implementation")
    return base, at, git(root, "rev-parse", "HEAD").stdout.strip()


def _provenance(root: Path, at: str, base: str) -> str | None:
    oracle_hash = "sha256:" + "0" * 64
    claim = Claim("c", "text", ("t",), {ORACLE_REL: oracle_hash})
    manifest = Manifest((claim,), (), ())
    return check_provenance(root, at, base, manifest, claim, b"")


def test_provenance_unknown_revision_error_names_the_git_failure(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _, _, head = _provenance_repo(root)
    with pytest.raises(Exception, match=GIT_FAILURE):
        _provenance(root, head, UNKNOWN)


def test_provenance_valid_negative_keeps_the_oracle_after_result(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    base, _, head = _provenance_repo(root)
    git(root, "checkout", "-q", "-b", "side", base)
    (root / "side.txt").write_text("side\n")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "side")
    side = git(root, "rev-parse", "HEAD").stdout.strip()
    assert _provenance(root, head, side) == AFTER
