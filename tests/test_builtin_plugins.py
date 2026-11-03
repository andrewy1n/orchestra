from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

import orchestra.plugins as plugins
from orchestra.canon.types import JsonValue
from orchestra.project_config import PluginName, ProjectConfig, StageName, load_project_config


def _write_config(
    root: Path,
    *,
    stage: StageName,
    selected: list[PluginName],
    runner: list[str],
) -> ProjectConfig:
    root.mkdir(parents=True, exist_ok=True)
    plugin_values = ", ".join(f'"{plugin}"' for plugin in selected)
    runner_values = ", ".join(f'"{item}"' for item in runner)
    path = root / "orchestra.toml"
    path.write_text(
        f"[verify.stages]\n{stage} = [{plugin_values}]\n\n"
        f"[verify.unit]\nrunner = [{runner_values}]\n",
        encoding="utf-8",
    )
    return load_project_config(root)


def _context(root: Path, stage: StageName) -> plugins.PluginContext:
    return plugins.PluginContext(
        root=root,
        stage=stage,
        revision="commit-123",
        tests=("tests/test_widget.py::test_widget",),
    )


def test_unit_stage_selects_configured_builtin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _write_config(
        tmp_path,
        stage="task",
        selected=["unit"],
        runner=["python", "-m", "pytest", "{tests}", "--junitxml={report}"],
    )
    monkeypatch.setattr(plugins, "run_tests", lambda root, tests, runner: {tests[0]: "passed"})

    results = plugins.dispatch_plugins(config, _context(tmp_path, "task"))

    assert [result.plugin_id for result in results] == ["unit"]
    assert results[0].revision == "commit-123"
    assert results[0].result == "pass"


def test_review_stage_builds_existing_reviewer_input(tmp_path: Path) -> None:
    config = _write_config(
        tmp_path,
        stage="phase",
        selected=["review"],
        runner=["python", "-m", "pytest", "{tests}", "--junitxml={report}"],
    )
    context = _context(tmp_path, "phase")
    record: dict[str, JsonValue] = {
        "record_type": "score:work-item",
        "subject": "task-a",
        "body": "review this behavior",
    }
    context = replace(
        context,
        review_records=(record,),
        phase_diff="+ expected behavior\n",
    )

    results = plugins.dispatch_plugins(config, context)

    assert [result.plugin_id for result in results] == ["review"]
    assert isinstance(results[0].output, str)
    assert "review this behavior" in results[0].output
    assert "+ expected behavior" in results[0].output


def test_exact_argv_reaches_process_without_shell_joining(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    argv = ["python", "-m", "pytest", "-o", "value with spaces", "{tests}", "--junitxml={report}"]
    config = _write_config(tmp_path, stage="task", selected=["unit"], runner=argv)
    captured: list[str] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        del kwargs
        captured.extend(command)
        return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr("orchestra.tuner.runner.subprocess.run", fake_run)

    results = plugins.dispatch_plugins(config, _context(tmp_path, "task"))

    assert [result.plugin_id for result in results] == ["unit"]
    assert captured[:6] == [
        "python",
        "-m",
        "pytest",
        "-o",
        "value with spaces",
        "tests/test_widget.py::test_widget",
    ]
    assert captured[6].startswith("--junitxml=")


def test_third_party_plugins_are_not_registered() -> None:
    assert plugins.registered_plugin_ids() == ("unit", "review")
