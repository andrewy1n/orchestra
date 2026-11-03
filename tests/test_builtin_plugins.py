from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

import orchestra.plugins as plugins
from orchestra.canon.project_config import PluginName, StageName
from orchestra.canon.types import JsonValue


def _write_config(
    root: Path,
    *,
    stage: StageName,
    selected: list[PluginName],
    runner: list[str],
) -> str:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=root, check=True)
    plugin_values = ", ".join(f'"{plugin}"' for plugin in selected)
    runner_values = ", ".join(json.dumps(item) for item in runner)
    path = root / "orchestra.toml"
    path.write_text(
        f"[verify.stages]\n{stage} = [{plugin_values}]\n\n"
        f"[verify.unit]\nrunner = [{runner_values}]\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "orchestra.toml"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "config"], cwd=root, check=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _context(root: Path, stage: StageName, revision: str) -> plugins.PluginContext:
    return plugins.PluginContext(
        root=root,
        stage=stage,
        revision=revision,
        tests=("tests/test_widget.py::test_widget",),
    )


def test_unit_stage_selects_configured_builtin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    revision = _write_config(
        tmp_path,
        stage="task",
        selected=["unit"],
        runner=["python", "-m", "pytest", "{tests}", "--junitxml={report}"],
    )
    monkeypatch.setattr(plugins, "run_tests", lambda root, tests, runner: {tests[0]: "passed"})

    results = plugins.dispatch_plugins(_context(tmp_path, "task", revision))

    assert [result.plugin_id for result in results] == ["unit"]
    assert results[0].revision == revision
    assert results[0].result == "pass"


def test_review_stage_builds_existing_reviewer_input(tmp_path: Path) -> None:
    revision = _write_config(
        tmp_path,
        stage="phase",
        selected=["review"],
        runner=["python", "-m", "pytest", "{tests}", "--junitxml={report}"],
    )
    context = _context(tmp_path, "phase", revision)
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

    results = plugins.dispatch_plugins(context)

    assert [result.plugin_id for result in results] == ["review"]
    assert isinstance(results[0].output, str)
    assert "review this behavior" in results[0].output
    assert "+ expected behavior" in results[0].output


def test_exact_argv_reaches_process_without_shell_joining(tmp_path: Path) -> None:
    captured_path = tmp_path / "captured.json"
    code = (
        "import json,pathlib,sys;"
        "argv=sys.argv[2:];"
        "pathlib.Path(sys.argv[1]).write_text(json.dumps(argv));"
        "report=next(arg.split('=',1)[1] for arg in argv if arg.startswith('--junitxml='));"
        'pathlib.Path(report).write_text(\'<testsuite><testcase classname="tests.test_widget" name="test_widget" /></testsuite>\')'
    )
    argv = [
        sys.executable,
        "-c",
        code,
        str(captured_path),
        "value with spaces",
        "{tests}",
        "--junitxml={report}",
    ]
    revision = _write_config(tmp_path, stage="task", selected=["unit"], runner=argv)

    results = plugins.dispatch_plugins(_context(tmp_path, "task", revision))

    assert [result.plugin_id for result in results] == ["unit"]
    captured = json.loads(captured_path.read_text())
    assert captured[:2] == [
        "value with spaces",
        "tests/test_widget.py::test_widget",
    ]
    assert captured[2].startswith("--junitxml=")


def test_third_party_plugins_are_not_registered() -> None:
    assert plugins.registered_plugin_ids() == ("unit", "review")
