from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import CANON_CMD

import orchestra.cli as cli
import orchestra.conductor.github_pr as github_pr
from orchestra.canon.project import open_store
from orchestra.canon.project_config import DEFAULT_RUNNER, load_project_config_at_revision
from orchestra.conductor.github_pr import GitHubCheck
from orchestra.tuner import plugins


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _init_repo(root: Path, branch: str = "main") -> None:
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q", "-b", branch)
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "test")


def _config_text(
    runner: tuple[str, ...] = DEFAULT_RUNNER,
    *,
    suite: tuple[str, str, str] | None = None,
    landing: bool = False,
) -> str:
    text = (
        '[verify.stages]\ntask = ["unit"]\nphase = ["unit", "review"]\n\n'
        f"[verify.unit]\nrunner = {json.dumps(runner)}\n"
    )
    if suite is not None:
        mode, command, gate = suite
        text += (
            f"\n[suite]\nmode = {json.dumps(mode)}\n"
            f"command = {json.dumps(command)}\ngate = {json.dumps(gate)}\n"
        )
    if landing:
        text += '\n[land]\nadapter = "github-pr"\nmerge = "human"\n'
    return text


def _commit_config(root: Path, text: str, message: str) -> str:
    (root / "orchestra.toml").write_text(text, encoding="utf-8")
    _git(root, "add", "orchestra.toml")
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD")


def test_missing_config_fails_clearly(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    result = cli.main(["suite", "policy", "--cwd", str(tmp_path)])

    assert result == 2
    assert "required project config is missing" in capsys.readouterr().err


def test_commit_pinned_runner_uses_the_target_revision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init_repo(tmp_path)
    runner_at_target = ("python3", "-m", "pytest", "--target", "{tests}", "--junitxml={report}")
    target = _commit_config(tmp_path, _config_text(runner_at_target), "target config")
    _commit_config(
        tmp_path,
        _config_text(("pytest", "--later", "{tests}", "--junitxml={report}")),
        "later config",
    )
    _git(tmp_path, "checkout", "-q", target)
    (tmp_path / "orchestra.toml").write_text(
        _config_text(("pytest", "--dirty", "{tests}", "--junitxml={report}")),
        encoding="utf-8",
    )
    captured: list[tuple[str, ...]] = []

    def run_tests(root: Path, tests: tuple[str, ...], runner: tuple[str, ...]) -> dict[str, str]:
        assert root == tmp_path
        assert tests == ("tests/test_widget.py::test_widget",)
        captured.append(runner)
        return {tests[0]: "passed"}

    monkeypatch.setattr(plugins, "run_tests", run_tests)
    result = plugins.dispatch_plugins(
        plugins.PluginContext(
            root=tmp_path,
            stage="task",
            revision=target,
            tests=("tests/test_widget.py::test_widget",),
        )
    )

    assert load_project_config_at_revision(tmp_path, target).runner == runner_at_target
    assert captured == [runner_at_target]
    assert result[0].revision == target


def test_exact_argv_reaches_the_configured_process(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    capture_file = tmp_path / "argv.json"
    code = (
        "import json,pathlib,sys;"
        "argv=sys.argv[2:];"
        "pathlib.Path(sys.argv[1]).write_text(json.dumps(argv));"
        "report=next(arg.split('=',1)[1] for arg in argv if arg.startswith('--junitxml='));"
        'pathlib.Path(report).write_text(\'<testsuite><testcase file="tests/test_widget.py" '
        'classname="tests.test_widget" name="test_widget" /></testsuite>\')'
    )
    runner = (
        sys.executable,
        "-c",
        code,
        str(capture_file),
        "value with spaces",
        "{tests}",
        "--junitxml={report}",
    )
    revision = _commit_config(tmp_path, _config_text(runner), "argv config")

    result = plugins.dispatch_plugins(
        plugins.PluginContext(
            root=tmp_path,
            stage="task",
            revision=revision,
            tests=("tests/test_widget.py::test_widget",),
        )
    )

    captured = json.loads(capture_file.read_text(encoding="utf-8"))
    assert captured[:2] == ["value with spaces", "tests/test_widget.py::test_widget"]
    assert len(captured) == 3
    assert captured[2].startswith("--junitxml=")
    assert result[0].result == "pass"


def test_suite_migration_uses_project_toml(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _init_repo(tmp_path)
    _commit_config(
        tmp_path,
        _config_text(suite=("smoke", "pytest -k from_toml", "required")),
        "suite config",
    )
    canon = tmp_path / ".canon"
    canon.mkdir()
    (canon / "config.json").write_text(
        json.dumps(
            {
                "settings": {
                    "conductor": {
                        "phase_gate": {
                            "suite": {
                                "mode": "full",
                                "command": "pytest -k from_canon",
                                "gate": "advisory",
                            }
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    result = cli.main(["suite", "policy", "--cwd", str(tmp_path)])

    assert result == 0
    policy = json.loads(capsys.readouterr().out)
    assert (policy["mode"], policy["command"], policy["gate"]) == (
        "smoke",
        "pytest -k from_toml",
        "required",
    )


def test_builtins_only_are_registered() -> None:
    assert plugins.registered_plugin_ids() == ("review", "unit")


def test_github_lifecycle_uses_packet_waits_and_reports_without_merge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _init_repo(tmp_path, branch="phase/project-config")
    (tmp_path / ".gitignore").write_text(".canon/\n", encoding="utf-8")
    _git(tmp_path, "add", ".gitignore")
    _git(tmp_path, "commit", "-qm", "ignore local store")
    revision = _commit_config(tmp_path, _config_text(landing=True), "landing config")
    (tmp_path / ".canon").mkdir()
    init = subprocess.run(
        [
            *CANON_CMD,
            "--root",
            str(tmp_path),
            "init",
            "--schemas",
            "score,conductor,tuner",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert init.returncode == 0, init.stdout + init.stderr
    project = open_store(tmp_path)
    packet_body = "## Look\nOpen the final phase proof.\n\n## Machine\nproof id\n\n## Attention\nnone\n\n## Diff\n1 file changed\n"
    project.create(
        record_type="score:effort",
        subject="workflow-loop",
        payload={"goal": "Project config integration", "kind": "deliver"},
    )
    project.create(
        record_type="score:phase",
        subject="project-config",
        payload={"title": "Project config", "ordinal": 1, "effort": "workflow-loop"},
        body=(
            "## Problem\n\nProject config policy is required.\n\n"
            "## Approach\n\nUse a configured adapter.\n\n"
            "## Exit criteria\n\nThe adapter reports completed CI.\n"
        ),
    )
    project.create(
        record_type="conductor:proof-packet",
        subject="project-config",
        payload={
            "phase": "project-config",
            "effort": "workflow-loop",
            "revision": revision,
            "base": "main",
            "kind": "claims",
        },
        body=packet_body,
    )

    class FakeGitHub:
        def __init__(self) -> None:
            self.events: list[str] = []
            self.body = ""
            self.poll = 0

        def push_branch(self, remote: str, branch: str) -> None:
            self.events.append(f"push:{remote}:{branch}")

        def repository(self) -> str:
            return "owner/repo"

        def create_pull_request(
            self, repository: str, head: str, base: str, title: str, body: str
        ) -> tuple[int, str]:
            self.events.append(f"create:{repository}:{head}:{base}:{title}")
            self.body = body
            return 42, "https://github.com/owner/repo/pull/42"

        def checks(self, repository: str, commit: str) -> tuple[GitHubCheck, ...]:
            self.poll += 1
            return (
                (GitHubCheck("CI", "in_progress", None),)
                if self.poll == 1
                else (GitHubCheck("CI", "completed", "success"),)
            )

        def statuses(self, repository: str, commit: str) -> tuple[str, ...]:
            return ("pending",) if self.poll == 1 else ("success",)

    github = FakeGitHub()
    monkeypatch.setattr(github_pr, "GitHubREST", lambda _root, _remote: github)
    monkeypatch.setattr(github_pr.time, "sleep", lambda _seconds: None)

    result = cli.main(["land", "--phase", "project-config", "--cwd", str(tmp_path)])

    assert result == 0
    assert github.body == packet_body
    assert github.poll == 2
    assert all("merge" not in event for event in github.events)
    output = capsys.readouterr().out
    assert '"result": "success"' in output
    assert "https://github.com/owner/repo/pull/42" in output
