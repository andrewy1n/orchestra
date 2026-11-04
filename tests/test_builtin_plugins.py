from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from orchestra.canon.project_config import PluginName, StageName
from orchestra.tuner import plugins


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


def test_review_stage_signs_actual_pass_verdict(tmp_path: Path) -> None:
    revision = _write_config(
        tmp_path,
        stage="phase",
        selected=["review"],
        runner=["python", "-m", "pytest", "{tests}", "--junitxml={report}"],
    )
    context = replace(
        _context(tmp_path, "phase", revision),
        reviewer_output=(
            "verdict: PASS\nfindings: []\nintegration:\n"
            "  interfaces: stable API\n  assumptions: host reviewer ran\n"
            "  invariants: signed evidence\n  conflicts: none\n"
        ),
    )

    results = plugins.dispatch_plugins(context)

    assert [result.plugin_id for result in results] == ["review"]
    assert results[0].result == "pass"
    assert results[0].output == {
        "verdict": "PASS",
        "reviewer_output": context.reviewer_output,
    }


def test_review_stage_maps_needs_work_and_rejects_invalid_output(tmp_path: Path) -> None:
    revision = _write_config(
        tmp_path,
        stage="phase",
        selected=["review"],
        runner=["python", "-m", "pytest", "{tests}", "--junitxml={report}"],
    )
    valid_prefix = (
        "verdict: NEEDS_WORK\nfindings:\n  - task: task-a\n"
        "    kind: behavior-bug\n    expected: correct behavior\n"
        "    observed: wrong behavior\n    severity: major\nintegration:\n"
        "  interfaces: stable API\n  assumptions: host reviewer ran\n"
        "  invariants: signed evidence\n  conflicts: none\n"
    )

    result = plugins.dispatch_plugins(
        replace(_context(tmp_path, "phase", revision), reviewer_output=valid_prefix)
    )[0]
    assert result.result == "fail"
    assert isinstance(result.output, dict)
    assert result.output["verdict"] == "NEEDS_WORK"

    invalid_findings = (
        valid_prefix.replace("    kind: behavior-bug\n", "    kind: unsupported-kind\n"),
        valid_prefix.replace("    severity: major\n", "    severity: high\n"),
    )
    for invalid in (
        None,
        "verdict: MAYBE",
        valid_prefix.replace("    kind: behavior-bug\n", ""),
        *invalid_findings,
    ):
        with pytest.raises(ValueError):
            plugins.dispatch_plugins(
                replace(_context(tmp_path, "phase", revision), reviewer_output=invalid)
            )


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


def test_builtins_use_installed_entry_points() -> None:
    assert plugins.registered_plugin_ids() == ("review", "unit")
