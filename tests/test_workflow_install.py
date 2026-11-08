from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_SKILLS = ("spec", "design", "tasks", "execute", "verify", "run")
RETIRED_SKILLS = ("settle-phase", "plan-phase", "execute-phase", "verify-work")


@pytest.fixture()
def roots(tmp_path: Path) -> tuple[Path, Path]:
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    home.mkdir()
    return project, home


def install(source: Path, roots: tuple[Path, Path]) -> subprocess.CompletedProcess[str]:
    project, home = roots
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["ORCHESTRA_INSTALL_SOURCE"] = str(source)
    env["PYTHONPATH"] = os.pathsep.join([str(REPO_ROOT), env.get("PYTHONPATH", "")]).strip(
        os.pathsep
    )
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "orchestra.cli",
            "install",
            "--only",
            "claude",
            "--home",
            str(home),
            "--copy",
        ],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def legacy_source(root: Path) -> Path:
    source = root / "legacy-source"
    for name in RETIRED_SKILLS:
        skill = source / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
    return source


def test_installed_payload_exposes_workflow_steps(roots: tuple[Path, Path]) -> None:
    result = install(REPO_ROOT, roots)
    assert result.returncode == 0, result.stdout + result.stderr

    skills = roots[1] / ".claude" / "skills"
    assert {name for name in WORKFLOW_SKILLS if (skills / name / "SKILL.md").is_file()} == set(
        WORKFLOW_SKILLS
    )
    assert not any((skills / name).exists() for name in RETIRED_SKILLS)


def test_upgrade_removes_managed_legacy_skills(tmp_path: Path, roots: tuple[Path, Path]) -> None:
    old_source = legacy_source(tmp_path)
    first = install(old_source, roots)
    assert first.returncode == 0, first.stdout + first.stderr

    upgraded = install(REPO_ROOT, roots)
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr

    skills = roots[1] / ".claude" / "skills"
    assert not any((skills / name).exists() for name in RETIRED_SKILLS)
    assert all((skills / name / "SKILL.md").is_file() for name in WORKFLOW_SKILLS)
    marker = json.loads((roots[1] / ".claude" / ".orchestra-install.json").read_text())
    assert all(f"skills/{name}" not in marker["entries"] for name in RETIRED_SKILLS)


def test_current_routes_resolve_installed_skills(roots: tuple[Path, Path]) -> None:
    result = install(REPO_ROOT, roots)
    assert result.returncode == 0, result.stdout + result.stderr

    skills = roots[1] / ".claude" / "skills"
    routes = (skills / "engage" / "SKILL.md").read_text(encoding="utf-8")
    playbook = (skills / "run" / "SKILL.md").read_text(encoding="utf-8")
    assert all(f"`{name}`" in playbook for name in WORKFLOW_SKILLS[:-1])
    assert all(f"`{name}`" in routes for name in ("spec", "tasks", "execute", "verify"))
