from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from canon_support import create, make_project
from conductor_support import FakeStates

from orchestra.canon.project import Project, open_store
from orchestra.canon.types import Record
from orchestra.conductor.landing import gate
from orchestra.conductor.phases.progress import close
from orchestra.conductor.tasks import wave

PHASE = "ph"
EFFORT = "ef"
BRANCH = "feature/ph"
PHASE_BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n"


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _commit(root: Path, name: str, text: str = "x\n") -> str:
    (root / name).write_text(text)
    _git(root, "add", name)
    _git(root, "commit", "-qm", name)
    return _git(root, "rev-parse", "HEAD")


@dataclass
class World:
    project: Project
    repo: Path
    tree: Path

    @property
    def default_tree(self) -> Path:
        return self.repo / ".worktrees" / PHASE

    def task_tree(self, slug: str) -> Path:
        return self.repo / ".worktrees" / f"{PHASE}--{slug}"


def _world(tmp_path: Path) -> World:
    repo = tmp_path / "repo"
    project = make_project(repo)
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    _commit(repo, "shared.txt", "base\n")
    _git(repo, "branch", "-M", "main")
    tree = tmp_path / "elsewhere" / "phase-tree"
    _git(repo, "worktree", "add", "-q", "-b", BRANCH, str(tree), "main")
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    landing = f"\n## Landing\n\nWorktree: {tree}\nBranch: {BRANCH}\nBase: main\n"
    create(
        project,
        "score:phase",
        PHASE,
        {"title": "Ph", "ordinal": 1, "effort": EFFORT},
        PHASE_BODY + landing,
    )
    return World(project, repo, tree)


def _item(project: Project, slug: str, **extra: object) -> Record:
    payload = {
        "title": slug,
        "phase": PHASE,
        "kind": "deliver",
        "assignee": "",
        "effort": EFFORT,
        "executor": "inline",
        **extra,
    }
    return create(
        project,
        "score:work-item",
        slug,
        payload,
        f"## Description\n\nDo {slug}.\n\n## Approach\n\nJust {slug}.",
    )


def _check_run(project: Project, acceptance: Record, revision: str, result: str) -> None:
    project.create(
        record_type="tuner:check-run",
        subject=acceptance["subject"],
        payload={
            "criterion_id": acceptance["id"],
            "revision": revision,
            "result": result,
            "effort": EFFORT,
            "method": "check",
            "signed_by": "",
            "runner": "orchestra",
            "exit_code": 0,
        },
    )


def _finish_task(world: World, slug: str, file: str, text: str) -> None:
    tree = world.task_tree(slug)
    tip = _commit(tree, file, text)
    acceptance = create(
        world.project,
        "score:acceptance",
        slug,
        {"method": "check", "phase": PHASE, "effort": EFFORT, "verify_command": "true"},
    )
    _check_run(world.project, acceptance, tip, "pass")
    item = world.project.resolve("score:work-item", slug)
    world.project.update(item["id"], record_type="score:work-item", transition="done")


def _start_tasks(world: World, *slugs: str) -> None:
    for slug in slugs:
        _item(world.project, slug)
    wave.start(world.project, world.repo, PHASE)


def _review(world: World, revision: str) -> None:
    world.project.create(
        record_type="tuner:check-run",
        subject=f"{PHASE}-review",
        payload={
            "criterion_id": f"{PHASE}-review",
            "revision": revision,
            "result": "pass",
            "effort": EFFORT,
            "method": "review",
            "signed_by": "",
            "evidence_kind": "review",
        },
    )


def _descent(world: World) -> gate.Term | None:
    terms = gate.gate_terms(open_store(world.repo), PHASE)
    return next((t for t in terms if t.name == "head-descends-from-review"), None)


def test_r13_gate_inspects_the_worktree_the_landing_section_names(tmp_path: Path) -> None:
    world = _world(tmp_path)
    _review(world, _git(world.tree, "rev-parse", "HEAD"))
    assert not world.default_tree.exists()

    term = _descent(world)

    assert term is not None
    assert term.holds, term.detail


def test_r13_gate_fails_when_the_named_worktree_changed_code_after_review(tmp_path: Path) -> None:
    world = _world(tmp_path)
    _review(world, _git(world.tree, "rev-parse", "HEAD"))
    _commit(world.tree, "late.py")

    term = _descent(world)

    assert term is not None
    assert not term.holds
    assert "late.py" in term.detail


def test_r13_gate_without_a_landing_section_looks_in_the_default_worktree(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    project = make_project(repo)
    _git(repo, "config", "user.email", "t@example.com")
    _commit(repo, "shared.txt")
    _git(repo, "branch", "-M", "main")
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    create(
        project,
        "score:phase",
        PHASE,
        {"title": "Ph", "ordinal": 1, "effort": EFFORT},
        PHASE_BODY,
    )
    assert [
        t for t in gate.gate_terms(open_store(repo), PHASE) if t.name == "head-descends-from-review"
    ] == []
    _git(repo, "worktree", "add", "-q", "-b", f"phase/{PHASE}", str(repo / ".worktrees" / PHASE))

    names = [t.name for t in gate.gate_terms(open_store(repo), PHASE)]

    assert "head-descends-from-review" in names


def test_r14_close_and_wave_use_the_worktree_and_branch_the_landing_section_names(
    tmp_path: Path,
) -> None:
    world = _world(tmp_path)
    _git(world.repo, "branch", f"phase/{PHASE}", "main")
    _start_tasks(world, "a")
    _finish_task(world, "a", "a.txt", "a\n")
    assert wave.end(world.project, world.repo, PHASE).merged == ("a",)
    tip = _git(world.tree, "rev-parse", "HEAD")
    create(
        world.project,
        "conductor:landing",
        PHASE,
        {
            "phase": PHASE,
            "effort": EFFORT,
            "number": 7,
            "url": "https://github.com/o/r/pull/7",
            "head_sha": tip,
            "result": "success",
        },
    )

    result = close.close_phase(
        world.project,
        world.repo,
        PHASE,
        FakeStates("MERGED", tip),
        reconcile_architecture=lambda *_: False,
    )

    assert result.ready, result.refusals
    assert not world.tree.exists()
    assert not world.task_tree("a").exists()
    assert _git(world.repo, "branch", "--list", BRANCH) == ""
    assert _git(world.repo, "branch", "--list", f"task/{PHASE}/*") == ""
    assert _git(world.repo, "branch", "--list", f"phase/{PHASE}") != ""
    assert world.project.resolve("score:phase", PHASE)["lifecycle_state"] == "done"


def test_r14_close_refuses_when_the_named_worktree_has_uncommitted_changes(
    tmp_path: Path,
) -> None:
    world = _world(tmp_path)
    tip = _git(world.tree, "rev-parse", "HEAD")
    (world.tree / "dirty.txt").write_text("dirty\n")
    create(
        world.project,
        "conductor:landing",
        PHASE,
        {
            "phase": PHASE,
            "effort": EFFORT,
            "number": 7,
            "url": "https://github.com/o/r/pull/7",
            "head_sha": tip,
            "result": "success",
        },
    )

    result = close.close_phase(
        world.project,
        world.repo,
        PHASE,
        FakeStates("MERGED", tip),
        reconcile_architecture=lambda *_: False,
    )

    assert not result.ready
    assert any(str(world.tree) in reason for reason in result.refusals)
    assert world.tree.is_dir()


def test_r14_close_refuses_when_the_named_branch_tip_differs_from_the_merged_head(
    tmp_path: Path,
) -> None:
    world = _world(tmp_path)
    create(
        world.project,
        "conductor:landing",
        PHASE,
        {
            "phase": PHASE,
            "effort": EFFORT,
            "number": 7,
            "url": "https://github.com/o/r/pull/7",
            "head_sha": "a" * 40,
            "result": "success",
        },
    )

    result = close.close_phase(
        world.project,
        world.repo,
        PHASE,
        FakeStates("MERGED", "a" * 40),
        reconcile_architecture=lambda *_: False,
    )

    assert not result.ready
    assert any(f"branch {BRANCH} tip" in reason for reason in result.refusals)


def test_r14_pending_close_sees_the_named_worktree_and_branch(tmp_path: Path) -> None:
    world = _world(tmp_path)
    record = world.project.resolve("score:phase", PHASE)
    world.project.update(record["id"], transition="in_progress")
    world.project.update(record["id"], transition="done")

    assert close.pending_close(world.project, world.repo, PHASE)

    _git(world.repo, "worktree", "remove", str(world.tree))
    assert close.pending_close(world.project, world.repo, PHASE)

    _git(world.repo, "branch", "-D", BRANCH)
    assert not close.pending_close(world.project, world.repo, PHASE)


def test_r15_wave_start_cuts_task_branches_from_the_named_branch(tmp_path: Path) -> None:
    world = _world(tmp_path)
    tip = _commit(world.tree, "named.txt")
    _item(world.project, "a")

    started = wave.start(world.project, world.repo, PHASE)

    assert [t.branch for t in started.tasks] == [f"task/{PHASE}/a"]
    assert started.tasks[0].write_root == str(world.task_tree("a"))
    assert _git(world.repo, "rev-parse", f"task/{PHASE}/a") == tip
    assert (world.task_tree("a") / "named.txt").is_file()


def test_r15_wave_start_runs_the_closing_task_in_the_named_worktree(tmp_path: Path) -> None:
    world = _world(tmp_path)
    _start_tasks(world, "a")
    _finish_task(world, "a", "a.txt", "a\n")
    assert wave.end(world.project, world.repo, PHASE).merged == ("a",)
    _item(world.project, f"verify-{PHASE}", depends_on=["a"])

    started = wave.start(world.project, world.repo, PHASE)

    assert started.execution_mode == "runner"
    closing = world.project.resolve("score:work-item", f"verify-{PHASE}")
    assert closing["payload"]["write_root"] == str(world.tree)


def test_r15_wave_end_merges_into_the_named_worktree(tmp_path: Path) -> None:
    world = _world(tmp_path)
    _start_tasks(world, "a")
    _finish_task(world, "a", "a.txt", "a\n")

    result = wave.end(world.project, world.repo, PHASE)

    assert result.merged == ("a",)
    assert (world.tree / "a.txt").is_file()
    assert not world.default_tree.exists()
    assert _git(world.repo, "merge-base", "--is-ancestor", f"task/{PHASE}/a", BRANCH) == ""


def _conflict(world: World) -> None:
    _start_tasks(world, "a", "b")
    _finish_task(world, "a", "shared.txt", "from a\n")
    _finish_task(world, "b", "shared.txt", "from b\n")
    assert wave.end(world.project, world.repo, PHASE).conflict == "b"


def test_r15_wave_resolve_refuses_while_the_named_worktree_holds_the_conflict(
    tmp_path: Path,
) -> None:
    world = _world(tmp_path)
    _conflict(world)

    result = wave.resolve(world.project, world.repo, PHASE, "b")

    assert not result.ready
    assert any("unmerged" in reason and "shared.txt" in reason for reason in result.refusals)


def test_r15_wave_resolve_commits_the_merge_in_the_named_worktree(tmp_path: Path) -> None:
    world = _world(tmp_path)
    _conflict(world)
    (world.tree / "shared.txt").write_text("from a\nfrom b\n")
    _git(world.tree, "add", "shared.txt")

    result = wave.resolve(world.project, world.repo, PHASE, "b")

    assert result.ready, result.refusals
    assert _git(world.tree, "rev-parse", "HEAD") == _git(world.repo, "rev-parse", BRANCH)
    assert _git(world.tree, "rev-parse", "HEAD") != result.commit or result.commit
    assert not world.default_tree.exists()
    assert not world.task_tree("resolve-b").exists()
