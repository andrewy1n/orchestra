from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
STRICT_ROOTS = (
    "orchestra/score",
    "orchestra/conductor",
    "orchestra/stage",
    "orchestra/cli.py",
    "orchestra/views.py",
)


@pytest.fixture(autouse=True)
def _disable_ci_for_temporary_type_probes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)


def _config() -> dict[str, object]:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        return tomllib.load(stream)


def _probe_project(tmp_path: Path) -> Path:
    tool_config = _config()["tool"]
    assert isinstance(tool_config, dict)
    basedpyright = tool_config["basedpyright"]
    assert isinstance(basedpyright, dict)
    strict = basedpyright["strict"]
    environments = basedpyright["executionEnvironments"]
    assert isinstance(strict, list)
    assert isinstance(environments, list)
    config = [
        "[tool.basedpyright]",
        'typeCheckingMode = "standard"',
        'pythonVersion = "3.10"',
        'include = ["orchestra"]',
        "strict = [" + ", ".join(json.dumps(root) for root in strict) + "]",
        "",
    ]
    for environment in environments:
        assert isinstance(environment, dict)
        config.extend(
            [
                "[[tool.basedpyright.executionEnvironments]]",
                f"root = {json.dumps(environment['root'])}",
                'extraPaths = ["."]',
            ]
        )
        if "reportExplicitAny" in environment:
            config.append(f"reportExplicitAny = {json.dumps(environment['reportExplicitAny'])}")
        config.append("")
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


def _probe_path(project: Path, root: str) -> Path:
    path = project / root
    if path.suffix != ".py":
        path = path / "probe.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@pytest.mark.parametrize("root", STRICT_ROOTS)
def test_strict_core_roots_reject_explicit_any(root: str, tmp_path: Path) -> None:
    project = _probe_project(tmp_path)
    probe = _probe_path(project, root)
    probe.write_text(
        "from typing import Any\n\ndef value(item: Any) -> Any:\n    return item\n",
        encoding="utf-8",
    )
    result = _typecheck(project, probe)
    assert result.returncode != 0, result.stdout
    assert "reportExplicitAny" in result.stdout, result.stdout


@pytest.mark.parametrize("root", STRICT_ROOTS)
def test_strict_core_roots_reject_unannotated_parameters(root: str, tmp_path: Path) -> None:
    project = _probe_project(tmp_path)
    probe = _probe_path(project, root)
    probe.write_text("def value(item):\n    return item\n", encoding="utf-8")
    result = _typecheck(project, probe)
    assert result.returncode != 0, result.stdout


def test_any_remains_allowed_outside_strict_roots(tmp_path: Path) -> None:
    project = _probe_project(tmp_path)
    probe = _probe_path(project, "orchestra")
    probe.write_text(
        "from typing import Any\n\ndef value(item: Any) -> Any:\n    return item\n",
        encoding="utf-8",
    )
    result = _typecheck(project, probe)
    assert result.returncode == 0, result.stdout


def test_strict_core_roots_have_explicit_any_errors() -> None:
    tool = _config()["tool"]
    assert isinstance(tool, dict)
    basedpyright = tool["basedpyright"]
    assert isinstance(basedpyright, dict)
    strict = basedpyright["strict"]
    environments = basedpyright["executionEnvironments"]
    assert isinstance(strict, list)
    assert isinstance(environments, list)
    for root in STRICT_ROOTS:
        assert root in strict
        assert any(
            isinstance(environment, dict)
            and environment.get("root") == root
            and environment.get("reportExplicitAny") == "error"
            for environment in environments
        )


def test_strict_core_baseline_has_no_target_entries() -> None:
    baseline = json.loads((ROOT / ".basedpyright" / "baseline.json").read_text(encoding="utf-8"))
    files = baseline.get("files", {})
    assert isinstance(files, dict)
    assert not any(any(root in path for root in STRICT_ROOTS) for path in files)


def test_tests_and_scripts_remain_standard() -> None:
    tool = _config()["tool"]
    assert isinstance(tool, dict)
    basedpyright = tool["basedpyright"]
    assert isinstance(basedpyright, dict)
    strict = basedpyright["strict"]
    assert isinstance(strict, list)
    assert not any(root.startswith("tests/") for root in strict)
    assert not any(root.startswith("scripts/") for root in strict)
