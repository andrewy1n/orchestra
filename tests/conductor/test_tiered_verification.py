"""Suite background runner, project suite policy, gate, and fix clustering."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

import helpers as h
import pytest
from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))

from orchestra.conductor.suite import (
    EVIDENCE_KIND,
    METHOD,
    SuitePolicy,
    SuiteResult,
    SuiteStart,
    build_suite_check_run_payload,
    cluster_by_module,
    module_fix_subject,
    parse_failing_node_ids,
    poll_suite,
    route_suite_failures,
    should_rerun_suite,
    start_suite_background,
    suite_subject,
)

SKILL = REPO_ROOT / "skills" / "execute" / "SKILL.md"

HEAD = "abcdef0123456789abcdef0123456789abcdef01"
PHASE = "verification-policy"


def _skill_text() -> str:
    return h.skill_text("verify")


def _skill_flat() -> str:
    return re.sub(r"\s+", " ", _skill_text())


def _git_worktree(tmp_path: Path) -> tuple[Path, str]:
    work = tmp_path / "wt"
    work.mkdir()
    subprocess.run(["git", "init"], cwd=work, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "t@example.com"],
        cwd=work,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "t"],
        cwd=work,
        check=True,
        capture_output=True,
    )
    (work / "README").write_text("x\n")
    subprocess.run(["git", "add", "README"], cwd=work, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=work,
        check=True,
        capture_output=True,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=work,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return work, head


def _suite_config(work: Path, mode: str, command: str = "") -> None:
    (work / "orchestra.toml").write_text(
        '[verify.stages]\nphase = ["unit"]\n[verify.unit]\n'
        'runner = ["pytest", "{tests}", "--junitxml={report}"]\n[suite]\n'
        f"mode = {json.dumps(mode)}\ncommand = {json.dumps(command)}\n"
    )


@pytest.mark.parametrize("mode", ["full", "smoke"])
def test_blank_local_command(tmp_path: Path, mode: str) -> None:
    from orchestra.canon.project_config import ProjectConfigError, load_project_config

    _suite_config(tmp_path, mode, "  ")
    with pytest.raises(ProjectConfigError, match=r"suite\.command"):
        load_project_config(tmp_path)


def test_skipped_start_exit(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from orchestra.cli import main

    work, _ = _git_worktree(tmp_path)
    _suite_config(work, "none")
    assert main(["suite", "start", "--cwd", str(work), "--phase", PHASE]) == 4
    assert json.loads(capsys.readouterr().out)["state"] == "skipped"


def test_skipped_suite_evidence(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from orchestra.cli import main

    work, _ = _git_worktree(tmp_path)
    _suite_config(work, "none")
    directory = work / ".suite"
    directory.mkdir()
    (directory / f"orchestra-suite-{PHASE}.exit").write_text("0")
    args = ["--cwd", str(work), "--phase", PHASE, "--allow-dirty"]
    main(["suite", "start", *args])
    capsys.readouterr()
    for action in ("poll", "collect"):
        assert main(["suite", action, *args]) == 4
        assert json.loads(capsys.readouterr().out)["result"] == "skipped"
    assert main(["suite", "record", *args, "--effort", "test"]) == 4
    assert "skipped" in capsys.readouterr().err


def test_background_worker_start_is_non_blocking(tmp_path: Path):
    work, head = _git_worktree(tmp_path)
    started = start_suite_background(
        worktree=work,
        phase_slug=PHASE,
        phase_head=head,
        log_dir=tmp_path / "logs",
        suite_command="echo ok",
        policy=SuitePolicy(mode="full", command="echo ok", gate="required"),
        allow_dirty=True,
    )
    assert isinstance(started, SuiteStart)
    assert started.blocking is False
    assert started.session_name.startswith("orchestra-suite-")
    assert poll_suite(started) is None


def test_runner_records_suite_check_run_payload_fields():
    suite = SuiteResult(
        exit_code=1,
        duration_s=12.5,
        output=("FAILED tests/test_foo.py::test_a\nFAILED tests/test_bar.py::test_b\n"),
        output_sha256="deadbeef" * 8,
        failing_node_ids=[
            "tests/test_foo.py::test_a",
            "tests/test_bar.py::test_b",
        ],
        result="fail",
        revision=HEAD,
    )
    payload = build_suite_check_run_payload(
        phase_slug=PHASE,
        effort="workflow-loop",
        suite=suite,
    )
    assert payload["revision"] == HEAD
    assert payload["exit_code"] == 1
    assert payload["duration_s"] == 12.5
    assert payload["output_sha256"] == "deadbeef" * 8
    assert payload["evidence_kind"] == EVIDENCE_KIND == "integration"
    assert payload["method"] == METHOD
    assert payload["runner"] == "orchestra"
    assert payload["failing_node_ids"] == [
        "tests/test_foo.py::test_a",
        "tests/test_bar.py::test_b",
    ]
    assert payload["criterion_id"] == suite_subject(PHASE)
    criterion_id = payload["criterion_id"]
    assert isinstance(criterion_id, str)
    assert criterion_id.endswith("-suite")
    assert not criterion_id.endswith("-tier2")


def test_suite_record_writes_runner_orchestra():
    """R2: suite check-run writer stamps payload.runner as orchestra."""
    suite = SuiteResult(
        exit_code=0,
        duration_s=1.0,
        output="1 passed\n",
        output_sha256="cafebabe" * 8,
        failing_node_ids=[],
        result="pass",
        revision=HEAD,
    )
    payload = build_suite_check_run_payload(
        phase_slug=PHASE,
        effort="workflow-loop",
        suite=suite,
    )
    assert payload["runner"] == "orchestra"


def test_worker_poll_collects_a_real_command_result(tmp_path: Path):
    work, head = _git_worktree(tmp_path)
    started = start_suite_background(
        worktree=work,
        phase_slug=PHASE,
        phase_head=head,
        suite_command="printf '1 passed\\n'",
        policy=SuitePolicy(mode="full", command="true", gate="required"),
        allow_dirty=True,
    )
    assert isinstance(started, SuiteStart)
    deadline = time.monotonic() + 5
    result = poll_suite(started)
    while result is None and time.monotonic() < deadline:
        time.sleep(0.02)
        result = poll_suite(started)

    assert result is not None
    assert result.exit_code == 0
    assert result.result == "pass"
    assert result.revision == head
    assert result.output == "1 passed\n"
    assert result.output_sha256
    assert result.failing_node_ids == []


def test_parse_failing_node_ids_and_digest_meta():
    output = """
=========================== FAILURES ===========================
FAILED tests/test_a.py::test_one - AssertionError
FAILED tests/test_b.py::TestCls::test_two - AssertionError
=========================== short test summary info ===========================
FAILED tests/test_a.py::test_one
FAILED tests/test_b.py::TestCls::test_two
"""
    nodes = parse_failing_node_ids(output)
    assert "tests/test_a.py::test_one" in nodes
    assert "tests/test_b.py::TestCls::test_two" in nodes
    suite = SuiteResult(
        exit_code=1,
        duration_s=1.0,
        output=output,
        output_sha256="abc",
        failing_node_ids=nodes,
        result="fail",
        revision=HEAD,
    )
    payload = build_suite_check_run_payload(
        phase_slug=PHASE,
        effort="workflow-loop",
        suite=suite,
    )
    assert "failing_node_ids" in payload
    assert payload["evidence_kind"] == "integration"
    assert "output_sha256" in payload


def test_mode_none_skips_suite_start(tmp_path: Path):
    work, head = _git_worktree(tmp_path)
    policy = SuitePolicy(mode="none", command="", gate="required")
    started = start_suite_background(
        worktree=work,
        phase_slug=PHASE,
        phase_head=head,
        policy=policy,
    )
    assert isinstance(started, SuiteStart)
    assert started.skipped is True
    polled = poll_suite(started)
    assert polled is not None
    assert polled.skipped is True


def test_mode_external_and_deferred_gate_do_not_run_locally(tmp_path: Path):
    work, head = _git_worktree(tmp_path)
    for policy in (
        SuitePolicy(mode="external", command="ci", gate="required"),
        SuitePolicy(mode="full", command="pytest -q", gate="deferred"),
        SuitePolicy(mode="smoke", command="pytest -q", gate="deferred"),
    ):
        started = start_suite_background(
            worktree=work,
            phase_slug=PHASE,
            phase_head=head,
            policy=policy,
        )
        assert isinstance(started, SuiteStart)
        assert started.skipped is True
        assert policy.run_locally is False


def test_mode_smoke_and_full_run_contracted_command(tmp_path: Path):
    work, head = _git_worktree(tmp_path)
    for mode in ("smoke", "full"):
        policy = SuitePolicy(mode=mode, command="printf suite-cmd", gate="required")
        started = start_suite_background(
            worktree=work,
            phase_slug=PHASE,
            phase_head=head,
            session_name=f"suite-{mode}",
            policy=policy,
            allow_dirty=True,
        )
        assert isinstance(started, SuiteStart)
        assert not started.skipped
        deadline = time.monotonic() + 5
        result = poll_suite(started)
        while result is None and time.monotonic() < deadline:
            time.sleep(0.02)
            result = poll_suite(started)
        assert result is not None
        assert result.result == "pass"
        assert result.output == "suite-cmd"


def test_advisory_full_policy_does_not_block_merge():
    policy = SuitePolicy(mode="full", command="pytest -q", gate="advisory")
    assert policy.blocks_merge is False
    assert policy.run_locally is True


def test_fix_cluster_budget_no_inline_rerun_for_required_gate():
    nodes = [
        "tests/test_foo.py::test_a",
        "tests/test_foo.py::test_b",
        "tests/test_bar.py::test_c",
    ]
    policy = SuitePolicy(mode="full", command="pytest", gate="required")
    clusters = cluster_by_module(nodes)
    assert set(clusters) == {"tests/test_foo.py", "tests/test_bar.py"}
    assert module_fix_subject("tests/test_foo.py") == "fix-test_foo"
    routed = route_suite_failures(
        nodes,
        fix_budget_remaining=1,
        policy=policy,
    )
    assert routed.reopen_done is False
    assert routed.inline_fix_and_rerun is False
    assert sum(routed.create_fix_flags) == 1
    assert routed.escalate is True
    routed2 = route_suite_failures(
        nodes,
        fix_budget_remaining=3,
        policy=policy,
    )
    assert sum(routed2.create_fix_flags) == 2
    assert all(s.startswith("fix-") for s in routed2.fix_subjects)
    assert should_rerun_suite(fix_tasks_created=sum(routed2.create_fix_flags))
    assert not should_rerun_suite(fix_tasks_created=0)
    flat = _skill_flat()
    assert "cluster" in flat or "failing test file" in flat or "module" in flat
    assert "inline" in flat and ("fix-and-rerun" in flat or "fix and rerun" in flat)
    assert "never reopen" in flat or ("never" in flat and "`done`" in flat)
    assert "retry" in flat and "budget" in flat


def test_execute_phase_documents_suite_policy_before_reviewer_and_check_run():
    text = (REPO_ROOT / "skills" / "verify" / "references" / "phase-end.md").read_text()
    flat = " ".join(text.split())
    assert "Do not waive suite policy" in flat
    assert (
        "`orchestra suite start` / `poll` / `collect` / `cancel` / `record` in the phase worktree"
        in flat
    )
    assert flat.index("closing verification → analyze → suite") < flat.index("→ reviewer")
    assert flat.index("→ reviewer") < flat.index("→ integration-report")
    assert flat.index("→ integration-report") < flat.index("→ phase gate")
    assert "orchestra suite record" in text
    assert (
        "subject `<phase-slug>-suite`, `evidence_kind: integration`, with runner metadata" in flat
    )


def test_execute_phase_documents_no_agent_waiver_of_suite_policy():
    flat = _skill_flat()
    assert "not waive" in flat
    assert "orchestra.toml" in flat or "suite policy" in flat
    assert "contract" in flat
    # red-first remains tdd-only; suite never red-first
    assert "never red-first" in flat


def test_evidence_kind_integration_not_regression():
    suite = SuiteResult(
        exit_code=0,
        duration_s=1.0,
        output="ok",
        output_sha256="x",
        failing_node_ids=[],
        result="pass",
        revision=HEAD,
    )
    payload = build_suite_check_run_payload(
        phase_slug=PHASE,
        effort="workflow-loop",
        suite=suite,
    )
    assert payload["evidence_kind"] == "integration"
    assert payload["evidence_kind"] != "regression"
    check = h.record_def("check-run")
    assert "failing_node_ids" in check["optional_payload"]
    assert "integration" in check["payload_enum"]["evidence_kind"]


def test_deferred_gate_is_landing_human_stop_not_local_block():
    policy = SuitePolicy(mode="full", command="pytest", gate="deferred")
    assert policy.deferred_landing_stop is True
    assert policy.run_locally is False
    assert policy.blocks_merge is False
    flat = _skill_flat()
    assert "deferred" in flat
    assert "Landing human stop" in flat or "human stop" in flat
