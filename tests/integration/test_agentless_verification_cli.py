from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Mapping
from pathlib import Path

import pytest
from conftest import REPO_ROOT, git, make_git_repo

PHASE = "runner-cli-phase"
EFFORT = "runner-cli-effort"
PHASE_BODY = (
    "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n\n"
    "## Requirements\n\nR1: Closing verification passes.\n\n"
    f"## Landing\n\nbranch: phase/{PHASE}\nworktree: <repo>/.worktrees/{PHASE}\nbase: main\n"
)


class World:
    def __init__(self, root: Path, landing: bool = True, acceptance: bool = True) -> None:
        self.repo = make_git_repo()
        (self.repo / "base.txt").write_text("base\n")
        git(self.repo, "add", "base.txt")
        git(self.repo, "commit", "-qm", "base")
        git(self.repo, "branch", "-M", "main")
        self.env = {
            key: value
            for key, value in os.environ.items()
            if key not in {"ORCHESTRA_STORE", "CANON_STORE", "VIRTUAL_ENV"}
        }
        self.env["HOME"] = str(root / "home")
        (root / "home").mkdir()
        self.ok("canon", "init", "--schemas", "score,conductor,tuner,composer")
        self.create("score:effort", EFFORT, {"goal": "g", "kind": "deliver"}, "")
        phase_body = PHASE_BODY if landing else PHASE_BODY.split("## Landing")[0]
        self.create(
            "score:phase",
            PHASE,
            {"title": PHASE, "ordinal": 1, "effort": EFFORT, "weight": "light"},
            phase_body,
        )
        if landing:
            git(self.repo, "branch", f"phase/{PHASE}", "main")
            (self.repo / ".worktrees").mkdir()
            git(
                self.repo,
                "worktree",
                "add",
                "-q",
                str(self.repo / ".worktrees" / PHASE),
                f"phase/{PHASE}",
            )
        self._dependency(acceptance=acceptance)

    def run(self, tool: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["uv", "run", "--quiet", "--project", str(REPO_ROOT), tool, *args],
            capture_output=True,
            text=True,
            cwd=str(self.repo),
            env=self.env,
        )

    def ok(self, tool: str, *args: str) -> str:
        result = self.run(tool, *args)
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout

    def create(
        self, record_type: str, subject: str, payload: Mapping[str, object], body: str
    ) -> str:
        result = self.ok(
            "canon",
            "create",
            "--type",
            record_type,
            "--subject",
            subject,
            "--payload",
            json.dumps(payload),
            "--body",
            body,
        )
        return str(json.loads(result)["record"]["id"])

    def update(self, record_id: str, *args: str) -> None:
        self.ok("canon", "update", "--type", "score:work-item", "--id", record_id, *args)

    def start(self) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        result = self.run("orchestra", "wave", "start", PHASE, "--json")
        try:
            payload: dict[str, object] = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {}
        return result, payload

    def state(self, slug: str) -> str:
        output = self.ok(
            "canon",
            "list",
            "--type",
            "score:work-item",
            "--subject",
            slug,
            "--exact-subject",
            "--format",
            "tsv",
            "--fields",
            "lifecycle_state",
        )
        return output.splitlines()[-1]

    def _dependency(
        self, *, executor: str = "subagent", report: bool = True, acceptance: bool = True
    ) -> None:
        dependency_id = self.create(
            "score:work-item",
            "implementation",
            {
                "title": "Implementation",
                "phase": PHASE,
                "kind": "deliver",
                "assignee": "",
                "effort": EFFORT,
                "executor": "inline",
                "requirements": [],
                "depends_on": [],
            },
            "## Description\n\nImplement.\n\n## Approach\n\nImplement.",
        )
        self.update(dependency_id, "--transition", "in_progress")
        self.update(dependency_id, "--transition", "done")
        phase_tree = self.repo / ".worktrees" / PHASE
        if report and phase_tree.is_dir():
            revision = git(phase_tree, "rev-parse", "HEAD").stdout.strip()
            self.create(
                "conductor:execution-report",
                "implementation",
                {
                    "work_item": "implementation",
                    "result": "pass",
                    "verdict": "pass",
                    "revision": revision,
                },
                "subject: implementation\nrevision: "
                + revision
                + "\nkind: deliver\nresult: pass\nverdict: pass\nevidence: done",
            )
        self.closing(executor=executor, acceptance=acceptance)

    def closing(
        self,
        *,
        executor: str = "subagent",
        command: str = "true",
        acceptance: bool = True,
    ) -> str:
        task_id = self.create(
            "score:work-item",
            "verify-runner",
            {
                "title": "Verify",
                "phase": PHASE,
                "kind": "deliver",
                "assignee": "",
                "effort": EFFORT,
                "executor": executor,
                "requirements": ["R1"],
                "depends_on": ["implementation"],
            },
            "## Description\n\nR1: Verify.\n\n## Approach\n\nRun checks.",
        )
        if acceptance:
            self.acceptance_id = self.acceptance(command)
        return task_id

    def acceptance(self, command: str, method: str = "check") -> str:
        return self.create(
            "score:acceptance",
            "verify-runner",
            {
                "method": method,
                "phase": PHASE,
                "effort": EFFORT,
                "verify_command": command,
                "requirement": "R1",
            },
            "",
        )

    def set_acceptance(self, command: str, method: str = "check") -> None:
        self.ok(
            "canon",
            "update",
            "--type",
            "score:acceptance",
            "--id",
            self.acceptance_id,
            "--payload",
            json.dumps({"verify_command": command, "method": method}),
        )


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


def test_r2_r10_closing_wave_runs_checks_and_closes_with_report(world: World) -> None:
    phase_tree = world.repo / ".worktrees" / PHASE
    head = git(phase_tree, "rev-parse", "HEAD")
    source = (phase_tree / "base.txt").read_text()

    result, output = world.start()

    assert result.returncode == 0, result.stdout + result.stderr
    assert output.get("execution_mode") == "runner"
    assert output.get("state") == "done"
    assert output.get("execution_report")
    assert output.get("refusal_reasons") == []
    checks = output.get("checks")
    assert isinstance(checks, list) and checks
    assert checks[0]["result"] == "pass"
    assert world.state("verify-runner") == "done"
    assert git(phase_tree, "rev-parse", "HEAD").stdout.strip() == head.stdout.strip()
    assert (phase_tree / "base.txt").read_text() == source


def test_r10_failed_runner_check_keeps_closing_task_open(world: World) -> None:
    world.set_acceptance("false")

    result, output = world.start()

    assert result.returncode == 1
    assert output.get("execution_mode") == "runner"
    assert output.get("state") == "in_progress"
    assert output.get("refusal_reasons")
    assert world.state("verify-runner") == "in_progress"


def test_r3_closing_task_waits_for_dependency_integration(tmp_path: Path) -> None:
    world = World(tmp_path)
    phase_tree = world.repo / ".worktrees" / PHASE
    base = git(phase_tree, "rev-parse", "HEAD").stdout.strip()
    (phase_tree / "unmerged.txt").write_text("work\n")
    git(phase_tree, "add", "unmerged.txt")
    git(phase_tree, "commit", "-qm", "implementation")
    task_tip = git(phase_tree, "rev-parse", "HEAD").stdout.strip()
    git(world.repo, "branch", f"task/{PHASE}/implementation", task_tip)
    git(phase_tree, "reset", "--hard", base)
    world.create(
        "conductor:execution-report",
        "implementation",
        {
            "work_item": "implementation",
            "result": "pass",
            "verdict": "pass",
            "revision": task_tip,
        },
        "subject: implementation\nrevision: "
        + task_tip
        + "\nkind: deliver\nresult: pass\nverdict: pass\nevidence: done",
    )

    result, output = world.start()

    assert result.returncode == 1
    assert output.get("execution_mode") == "runner"
    reasons = output.get("refusal_reasons")
    assert isinstance(reasons, list)
    assert any(isinstance(reason, str) and "integrat" in reason.lower() for reason in reasons)
    assert world.state("verify-runner") == "planned"


def test_closing_task_without_landing_uses_agent_path(tmp_path: Path) -> None:
    world = World(tmp_path, landing=False)

    result, output = world.start()

    assert result.returncode == 0, result.stdout + result.stderr
    assert output.get("execution_mode") == "agent"
    assert output.get("tasks")
    assert world.state("verify-runner") == "in_progress"


def test_closing_manual_acceptance_waits_for_human(world: World) -> None:
    world.set_acceptance("true", method="manual")

    result, output = world.start()

    assert result.returncode == 3
    assert output.get("execution_mode") == "runner"
    assert output.get("state") == "in_progress"
    checks = output.get("checks")
    assert isinstance(checks, list) and checks
    first_check = checks[0]
    assert isinstance(first_check, dict)
    assert first_check.get("exit_code") == 3
    assert first_check.get("result") == "pending"
    assert world.state("verify-runner") == "in_progress"


def test_closing_task_with_no_acceptance_reports_refusal(tmp_path: Path) -> None:
    world = World(tmp_path, acceptance=False)

    result, output = world.start()

    assert result.returncode == 1
    assert output.get("execution_mode") == "runner"
    reasons = output.get("refusal_reasons")
    assert isinstance(reasons, list)
    assert any(
        "no active acceptance checks" in reason for reason in reasons if isinstance(reason, str)
    )
    assert world.state("verify-runner") == "in_progress"


def test_failed_closing_runner_can_retry_and_close(world: World) -> None:
    world.set_acceptance("false")
    first, first_output = world.start()
    assert first.returncode == 1
    assert first_output.get("state") == "in_progress"
    world.set_acceptance("true")

    second, second_output = world.start()

    assert second.returncode == 0, second.stdout + second.stderr
    assert second_output.get("execution_mode") == "runner"
    assert second_output.get("state") == "done"
    assert world.state("verify-runner") == "done"


def test_closing_executor_override_does_not_dispatch_an_agent(world: World) -> None:
    result, output = world.start()

    assert result.returncode == 0, result.stdout + result.stderr
    assert output.get("execution_mode") == "runner"
    assert "tasks" not in output
