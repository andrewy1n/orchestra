"""Oracles for removing the Textual dashboard: no Textual code, tmux plugin, or stale references remain."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

from conftest import REPO_ROOT

PYPROJECT = REPO_ROOT / "pyproject.toml"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"
PYTEST_INI = REPO_ROOT / "pytest.ini"
README = REPO_ROOT / "README.md"
BASELINE = REPO_ROOT / ".basedpyright" / "baseline.json"
DASHBOARD = REPO_ROOT / "dashboard"
BACKEND = DASHBOARD / "backend"


def python_files() -> list[Path]:
    found = []
    for top in ("dashboard", "orchestra"):
        for path in sorted((REPO_ROOT / top).rglob("*.py")):
            if {"node_modules", "__pycache__"} & set(path.parts):
                continue
            found.append(path)
    return found


def imported_top_levels(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def files_importing(package: str) -> list[str]:
    return [
        str(path.relative_to(REPO_ROOT))
        for path in python_files()
        if package in imported_top_levels(path)
    ]


def dependency_names() -> set[str]:
    text = PYPROJECT.read_text()
    block = re.search(r"^dependencies\s*=\s*\[(.*?)\]", text, re.DOTALL | re.MULTILINE)
    assert block, "pyproject.toml has no dependencies list"
    names = set()
    for entry in re.findall(r'"([^"]+)"', block.group(1)):
        match = re.match(r"[A-Za-z0-9_.-]+", entry)
        assert match, entry
        names.add(match.group(0).lower().replace("_", "-"))
    return names


def test_r1_no_python_file_imports_textual():
    assert files_importing("textual") == []


def test_r2_pyproject_does_not_list_textual():
    assert "textual" not in dependency_names()


def test_r3_rich_is_listed_only_if_a_surviving_module_imports_it():
    assert files_importing("textual") == []
    assert not (DASHBOARD / "app.py").exists()
    importers = files_importing("rich")
    assert ("rich" in dependency_names()) == bool(importers), importers


def test_r4_tmux_plugin_files_are_gone():
    present = [
        path
        for path in ("orchestra.tmux", "dashboard/bin/dashboard", "dashboard/bin/dashboard-status")
        if (REPO_ROOT / path).exists()
    ]
    assert present == []


def test_r5_ci_has_no_tmux_job_and_pytest_has_no_tmux_marker():
    yaml = pytest.importorskip("yaml")
    workflow = yaml.safe_load(CI.read_text())
    jobs = workflow["jobs"]
    tmux_jobs = [
        name
        for name, spec in jobs.items()
        if "tmux" in name.lower() or "tmux" in str(spec.get("name", "")).lower()
    ]
    assert tmux_jobs == []
    tmux_steps = [
        step["run"]
        for spec in jobs.values()
        for step in spec.get("steps", [])
        if "run" in step and "tmux" in step["run"].lower()
    ]
    assert tmux_steps == []
    assert "tmux" not in PYTEST_INI.read_text().lower()


def test_r6_no_module_sits_directly_under_dashboard():
    modules = sorted(path.name for path in DASHBOARD.glob("*.py") if path.name != "__init__.py")
    assert modules == []


def test_r7_survivors_live_under_backend_and_server_under_backend_server():
    expected = (
        "records",
        "task",
        "phase",
        "snapshot",
        "journal",
        "gates",
        "landing",
        "approval",
        "backlog",
        "dismiss",
    )
    missing = [name for name in expected if not (BACKEND / f"{name}.py").is_file()]
    assert missing == []
    server = BACKEND / "server"
    missing_server = [
        name for name in ("app.py", "service.py", "__main__.py") if not (server / name).is_file()
    ]
    assert missing_server == []


def test_r11_readme_has_no_tmux_dashboard_section():
    text = README.read_text()
    headings = [
        line
        for line in text.splitlines()
        if re.match(r"#{1,6}\s", line) and "tmux" in line.lower() and "dashboard" in line.lower()
    ]
    assert headings == []
    assert "orchestra.tmux" not in text
    assert "dashboard/bin/dashboard" not in text.replace("dashboard/bin/web", "")


def test_r12_basedpyright_baseline_names_no_deleted_file():
    assert BASELINE.is_file()
    files = json.loads(BASELINE.read_text())["files"]
    assert files
    deleted = [name for name in files if not (REPO_ROOT / name).exists()]
    assert deleted == []
