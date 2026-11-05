from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from canon_support import REPO, create, make_project

from orchestra.canon.project import Project

GATES = "Plan-review gates for every phase are preauthorized; plan and execute each phase without stopping."
PROMOTE = "Plan and promote each next phase without asking once the current one closes."
UNRELATED = "The code lives in this plugin repo under scripts/ and skills/."


def _cli(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(REPO))
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "effort", "autonomy", *args],
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
    )


def _constraint(project: Project, subject: str, effort: str, statement: str) -> None:
    create(
        project,
        "score:constraint",
        subject,
        {"statement": statement, "applies_to": "all", "effort": effort},
    )


def _world(tmp_path: Path) -> Project:
    project = make_project(tmp_path)
    for effort in ("alpha", "beta", "gamma"):
        create(project, "score:effort", effort, {"goal": "g", "kind": "deliver"})
    _constraint(project, "alpha-gates", "alpha", GATES)
    _constraint(project, "beta-gates", "beta", GATES)
    _constraint(project, "beta-promote", "beta", PROMOTE)
    _constraint(project, "gamma-misc", "gamma", UNRELATED)
    return project


def _level(project: Project, effort: str) -> str:
    return str(project.resolve("score:effort", effort)["payload"].get("autonomy", "gated"))


def test_r05_sets_the_level_through_a_supersede(tmp_path: Path) -> None:
    project = _world(tmp_path)
    result = _cli(tmp_path, "alpha", "auto-plan", "--json")
    assert result.returncode == 0, result.stderr
    assert _level(project, "alpha") == "auto-plan"
    states = sorted(
        r["lifecycle_state"] for r in project.list("score:effort") if r["subject"] == "alpha"
    )
    assert states == ["active", "superseded"]


def test_r05_rejects_an_unknown_level_and_an_unknown_effort(tmp_path: Path) -> None:
    project = _world(tmp_path)
    assert _cli(tmp_path, "alpha", "yolo").returncode == 2
    assert _cli(tmp_path, "nope", "gated").returncode == 2
    assert _level(project, "alpha") == "gated"


def test_r07_migrate_without_apply_prints_the_mapping_and_writes_nothing(tmp_path: Path) -> None:
    project = _world(tmp_path)
    result = _cli(tmp_path, "--migrate", "--json")
    assert result.returncode == 0, result.stderr
    rows = json.loads(result.stdout)["mappings"]
    assert {(r["constraint"], r["level"]) for r in rows} == {
        ("alpha-gates", "auto-plan"),
        ("beta-gates", "auto-plan"),
        ("beta-promote", "auto-phases"),
    }
    assert _level(project, "alpha") == "gated"
    active = [r for r in project.list("score:constraint") if r["lifecycle_state"] == "active"]
    assert len(active) == 4


def test_r07_apply_gives_each_effort_its_strongest_matching_level(tmp_path: Path) -> None:
    project = _world(tmp_path)
    result = _cli(tmp_path, "--migrate", "--apply")
    assert result.returncode == 0, result.stderr
    assert _level(project, "alpha") == "auto-plan"
    assert _level(project, "beta") == "auto-phases"
    assert _level(project, "gamma") == "gated"


def test_r08_apply_retires_each_migrated_constraint_naming_the_replacing_field(
    tmp_path: Path,
) -> None:
    project = _world(tmp_path)
    assert _cli(tmp_path, "--migrate", "--apply").returncode == 0
    statements = {
        r["subject"]: str(r["payload"]["statement"])
        for r in project.list("score:constraint")
        if r["lifecycle_state"] == "active"
    }
    assert (
        statements["alpha-gates"]
        == "Retired: replaced by the effort field autonomy=auto-plan on alpha."
    )
    assert "autonomy=auto-phases on beta" in statements["beta-promote"]
    assert statements["gamma-misc"] == UNRELATED


def test_r08_a_second_apply_changes_nothing(tmp_path: Path) -> None:
    project = _world(tmp_path)
    assert _cli(tmp_path, "--migrate", "--apply").returncode == 0
    before = len(project.records())
    second = _cli(tmp_path, "--migrate", "--apply", "--json")
    assert second.returncode == 0, second.stderr
    assert json.loads(second.stdout)["mappings"] == []
    assert len(project.records()) == before
