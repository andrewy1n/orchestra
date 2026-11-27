"""The store guard repairs through the real entry points: `canon` and `orchestra`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import git

from integration.test_gate_repairs_e2e import EFFORT, PHASE, World, _seed_phase


@pytest.fixture
def world(tmp_path: Path) -> World:
    world = World(tmp_path)
    world.canon("init", "--schemas", "score,conductor,tuner,composer")
    return world


def _gate(world: World) -> tuple[int, str]:
    result = world.run("orchestra", "gate", PHASE, "--store", str(world.store))
    return result.returncode, result.stdout + result.stderr


def _extra_acceptance(world: World) -> dict:
    return world.create(
        "score:acceptance",
        f"{PHASE}-extra",
        {
            "criterion": "unchecked",
            "method": "check",
            "phase": PHASE,
            "effort": EFFORT,
            "verify_command": "true",
            "requirement": "R2",
        },
    )


def test_noop_supersede_is_refused_and_writes_nothing(world: World) -> None:
    record = world.create("score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    before = world.run("canon", "get", "--type", "score:effort", "--id", record["id"])
    listed = world.run("canon", "list", "--type", "score:effort")

    refused = world.run(
        "canon",
        "supersede",
        "--type",
        "score:effort",
        "--id",
        record["id"],
        "--payload",
        json.dumps({"goal": "g", "kind": "deliver"}),
    )

    assert refused.returncode != 0
    assert record["id"] in refused.stdout + refused.stderr
    assert world.run("canon", "list", "--type", "score:effort").stdout == listed.stdout
    after = world.run("canon", "get", "--type", "score:effort", "--id", record["id"])
    assert after.stdout == before.stdout


def test_changing_supersede_still_writes_a_successor(world: World) -> None:
    record = world.create("score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    result = world.run(
        "canon",
        "supersede",
        "--type",
        "score:effort",
        "--id",
        record["id"],
        "--payload",
        json.dumps({"goal": "changed", "kind": "deliver"}),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["record"]["id"] != record["id"]


def test_retired_acceptance_is_ignored_by_the_gate(world: World) -> None:
    _seed_phase(world)
    assert _gate(world)[0] == 0
    extra = _extra_acceptance(world)
    blocked, output = _gate(world)
    assert blocked != 0, output

    retired = world.canon(
        "update",
        "--type",
        "score:acceptance",
        "--id",
        extra["id"],
        "--transition",
        "retired",
        "--expected-revision",
        extra["revision"],
    )

    assert retired["lifecycle_state"] == "retired"
    code, output = _gate(world)
    assert code == 0, output


def test_gate_accepts_a_clean_base_merge_after_review(world: World) -> None:
    code, _ = _seed_phase(world)
    worktree = code / ".worktrees" / PHASE
    (code / "base.txt").write_text("base\n")
    git(code, "add", "base.txt")
    git(code, "commit", "-qm", "base work")
    merged = git(worktree, "merge", "-q", "--no-ff", "-m", "merge main", "main")
    assert merged.returncode == 0, merged.stdout + merged.stderr

    status, output = _gate(world)

    assert status == 0, output


def test_gate_refuses_a_phase_edit_after_review(world: World) -> None:
    code, _ = _seed_phase(world)
    worktree = code / ".worktrees" / PHASE
    (worktree / "landed.txt").write_text("edited\n")
    git(worktree, "commit", "-qam", "edit after review")

    status, output = _gate(world)

    assert status != 0
    assert "landed.txt" in output
