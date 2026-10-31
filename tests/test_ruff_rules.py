"""Ruff and baseline policy requirements."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

from conftest import REPO_ROOT


def _ruff_settings() -> str:
    return (REPO_ROOT / "pyproject.toml").read_text()


def test_r1_rule_set() -> None:
    match = re.search(r"(?ms)^\[tool\.ruff\.lint\]\s*(.*?)(?=^\[|\Z)", _ruff_settings())
    assert match is not None
    select = re.search(r"(?m)^select\s*=\s*\[([^]]*)\]", match.group(1))
    assert select is not None
    assert set(re.findall(r"['\"]([^'\"]+)['\"]", select.group(1))) == {
        "E",
        "F",
        "I",
        "B",
        "UP",
        "SIM",
        "RUF",
        "ERA",
    }


def test_r2_ignored_line_length() -> None:
    assert re.search(r"(?m)^ignore\s*=\s*\[[^]]*['\"]E501['\"]", _ruff_settings())


def test_r3_line_length() -> None:
    assert re.search(r"(?m)^line-length\s*=\s*100\s*$", _ruff_settings())


def test_r6_pinned_lint() -> None:
    workflow = (REPO_ROOT / ".github/workflows/ci.yml").read_text()
    checks_job = re.search(r"(?ms)^  checks:\n(.*?)(?=^  [\w-]+:|\Z)", workflow)
    assert checks_job is not None
    assert re.search(
        r"(?m)^\s*- run: uvx ruff@0\.13\.1 check \.\s*$", checks_job.group(1)
    )


def test_r7_pinned_format() -> None:
    workflow = (REPO_ROOT / ".github/workflows/ci.yml").read_text()
    checks_job = re.search(r"(?ms)^  checks:\n(.*?)(?=^  [\w-]+:|\Z)", workflow)
    assert checks_job is not None
    assert re.search(
        r"(?m)^\s*- run: uvx ruff@0\.13\.1 format --check \.\s*$",
        checks_job.group(1),
    )


def _ruff_rejects(source: str, command: str, expected: str) -> bool:
    with tempfile.TemporaryDirectory(prefix="orchestra-ruff-") as temp_dir:
        source_path = Path(temp_dir) / "sample.py"
        source_path.write_text(source)
        result = subprocess.run(
            [
                "uvx",
                "ruff@0.13.1",
                *command.split(),
                "--config",
                str(REPO_ROOT / "pyproject.toml"),
                str(source_path),
            ],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            check=False,
        )
    output = result.stdout + result.stderr
    return (
        result.returncode != 0 and expected in output and "error:" not in output.lower()
    )


def test_r8_unsorted_imports_fail() -> None:
    source = "import sys\nimport os\n\nprint(sys.platform, os.name)\n"
    assert _ruff_rejects(source, "check", "I001")


def test_r9_unformatted_file_fails() -> None:
    assert _ruff_rejects("value = [1,2,3]\n", "format --check", "Would reformat")


def test_r11_baseline_count() -> None:
    baseline = json.loads((REPO_ROOT / ".basedpyright/baseline.json").read_text())
    assert sum(len(entries) for entries in baseline["files"].values()) <= 19


def test_r12_agent_lint() -> None:
    agents = re.sub(r"\s+", " ", (REPO_ROOT / "AGENTS.md").read_text().lower())
    assert "ruff check" in agents and "before you close a task" in agents


def test_r13_agent_format() -> None:
    agents = re.sub(r"\s+", " ", (REPO_ROOT / "AGENTS.md").read_text().lower())
    assert "ruff format" in agents and "before you close a task" in agents


def test_r14_readme_lint() -> None:
    readme = (REPO_ROOT / "README.md").read_text()
    assert re.search(r"\buvx ruff@0\.13\.1 check\b", readme)


def test_r15_readme_format() -> None:
    readme = (REPO_ROOT / "README.md").read_text()
    assert re.search(r"\buvx ruff@0\.13\.1 format --check\b", readme)
