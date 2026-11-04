from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # pyright: ignore[reportMissingImports]  # Pytest installs tomli on Python 3.10.

ROOT = Path(__file__).resolve().parents[1]
STRICT_ROOT = "orchestra/sessions"


@pytest.fixture(autouse=True)
def _disable_ci_for_temporary_type_probes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)


def _config() -> dict[str, object]:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        return tomllib.load(stream)


def _probe_project(tmp_path: Path) -> Path:
    tool = _config()["tool"]
    assert isinstance(tool, dict)
    basedpyright = tool["basedpyright"]
    assert isinstance(basedpyright, dict)
    strict = basedpyright["strict"]
    assert isinstance(strict, list)
    config = [
        "[tool.basedpyright]",
        'typeCheckingMode = "standard"',
        'pythonVersion = "3.10"',
        'include = ["orchestra"]',
        "strict = " + json.dumps(strict),
        'reportExplicitAny = "error"',
        "",
    ]
    (tmp_path / "pyproject.toml").write_text("\n".join(config), encoding="utf-8")
    return tmp_path


def _typecheck(project: Path, probe: Path) -> subprocess.CompletedProcess[str]:
    basedpyright = Path(sys.executable).with_name("basedpyright")
    return subprocess.run(
        [str(basedpyright), "--project", str(project / "pyproject.toml"), str(probe)],
        cwd=project,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def test_strict_root_config() -> None:
    tool = _config()["tool"]
    assert isinstance(tool, dict)
    basedpyright = tool["basedpyright"]
    assert isinstance(basedpyright, dict)
    strict = basedpyright["strict"]
    assert isinstance(strict, list)
    assert basedpyright["reportExplicitAny"] == "error"
    assert "orchestra" in strict or STRICT_ROOT in strict


def test_explicit_any_is_rejected(tmp_path: Path) -> None:
    project = _probe_project(tmp_path)
    probe = project / STRICT_ROOT / "probe.py"
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_text(
        "from typing import Any\n\ndef value(item: Any) -> Any:\n    return item\n",
        encoding="utf-8",
    )
    result = _typecheck(project, probe)
    assert result.returncode != 0, result.stdout
    assert "reportExplicitAny" in result.stdout


def test_unannotated_parameter_is_rejected(tmp_path: Path) -> None:
    project = _probe_project(tmp_path)
    probe = project / STRICT_ROOT / "probe.py"
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_text("def value(item):\n    return item\n", encoding="utf-8")
    result = _typecheck(project, probe)
    assert result.returncode != 0, result.stdout


def test_any_is_rejected_outside_strict_root(tmp_path: Path) -> None:
    project = _probe_project(tmp_path)
    probe = project / "orchestra" / "other" / "probe.py"
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_text(
        "from typing import Any\n\ndef value(item: Any) -> Any:\n    return item\n",
        encoding="utf-8",
    )
    result = _typecheck(project, probe)
    assert result.returncode != 0, result.stdout
    assert "reportExplicitAny" in result.stdout


def test_baseline_has_no_sessions_entries() -> None:
    assert not (ROOT / ".basedpyright" / "baseline.json").exists()


def test_tests_standard_mode() -> None:
    tool = _config()["tool"]
    assert isinstance(tool, dict)
    basedpyright = tool["basedpyright"]
    assert isinstance(basedpyright, dict)
    strict = basedpyright["strict"]
    assert isinstance(strict, list)
    assert not any(root.startswith("tests/") for root in strict)


def test_scripts_standard_mode() -> None:
    tool = _config()["tool"]
    assert isinstance(tool, dict)
    basedpyright = tool["basedpyright"]
    assert isinstance(basedpyright, dict)
    strict = basedpyright["strict"]
    assert isinstance(strict, list)
    assert not any(root.startswith("scripts/") for root in strict)
