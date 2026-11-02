from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
TUNER_ROOT = "orchestra/tuner"


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
        'include = ["orchestra", "tests", "scripts"]',
        "strict = " + json.dumps(strict),
        "",
    ]
    for environment in environments:
        assert isinstance(environment, dict)
        config.extend(
            [
                "[[tool.basedpyright.executionEnvironments]]",
                "root = " + json.dumps(environment["root"]),
                'extraPaths = ["."]',
            ]
        )
        if "reportExplicitAny" in environment:
            config.append("reportExplicitAny = " + json.dumps(environment["reportExplicitAny"]))
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


def _write_probe(project: Path, root: str, source: str) -> Path:
    probe = project / root / "probe.py"
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_text(source, encoding="utf-8")
    return probe


def test_tuner_rejects_explicit_any(tmp_path: Path) -> None:
    project = _probe_project(tmp_path)
    probe = _write_probe(
        project,
        TUNER_ROOT,
        "from typing import Any\n\ndef value(item: Any) -> Any:\n    return item\n",
    )
    result = _typecheck(project, probe)
    assert result.returncode != 0, result.stdout
    assert "reportExplicitAny" in result.stdout, result.stdout


def test_tuner_rejects_unannotated_parameters(tmp_path: Path) -> None:
    project = _probe_project(tmp_path)
    probe = _write_probe(project, TUNER_ROOT, "def value(item):\n    return item\n")
    result = _typecheck(project, probe)
    assert result.returncode != 0, result.stdout


def test_standard_mode_keeps_tests_and_scripts_outside_strict_roots(tmp_path: Path) -> None:
    tool = _config()["tool"]
    assert isinstance(tool, dict)
    basedpyright = tool["basedpyright"]
    assert isinstance(basedpyright, dict)
    strict = basedpyright["strict"]
    assert isinstance(strict, list)
    assert not any(root.startswith("tests/") for root in strict)
    assert not any(root.startswith("scripts/") for root in strict)

    project = _probe_project(tmp_path)
    probe = _write_probe(
        project,
        "tests",
        "from typing import Any\n\ndef value(item: Any) -> Any:\n    return item\n",
    )
    result = _typecheck(project, probe)
    assert result.returncode == 0, result.stdout


def test_baseline_has_no_tuner_entries() -> None:
    baseline = json.loads((ROOT / ".basedpyright" / "baseline.json").read_text(encoding="utf-8"))
    files = baseline.get("files", {})
    assert isinstance(files, dict)
    assert not any(path.lstrip("./").startswith(TUNER_ROOT) for path in files)


def test_import_boundary() -> None:
    violations: list[str] = []
    for path in (ROOT / TUNER_ROOT).rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules = [node.module]
            else:
                continue
            for module in modules:
                if module.startswith("orchestra.") and not module.startswith(
                    ("orchestra.canon", "orchestra.tuner")
                ):
                    violations.append(f"{path.relative_to(ROOT)}:{node.lineno}: {module}")
    assert violations == []
