"""Suite background runner, phase_gate.suite policy, gate, and fix clustering."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from conftest import REPO_ROOT
from skill_extraction import extract_invocations

sys.path.insert(0, str(REPO_ROOT))

from orchestra.suite import (  # noqa: E402
    EVIDENCE_KIND,
    METHOD,
    SuitePolicy,
    SuiteResult,
    SuiteStart,
    advisory_finding_payload,
    build_suite_check_run_payload,
    cluster_by_module,
    load_suite_policy,
    module_fix_subject,
    normalize_suite_policy,
    orphan_recovery_hint,
    parse_failing_node_ids,
    phase_suite_gate_holds,
    poll_suite,
    readme_suite_command,
    route_suite_failures,
    should_rerun_suite,
    start_suite_background,
    suite_subject,
)

SKILL = REPO_ROOT / "skills" / "execute-phase" / "SKILL.md"
README = REPO_ROOT / "README.md"
CONTRACT = REPO_ROOT / "contract" / "project-design.json"
LIVE_DESIGN = REPO_ROOT / ".artifacts" / "project-design.json"

HEAD = "abcdef0123456789abcdef0123456789abcdef01"
PHASE = "verification-policy"


def _skill_text() -> str:
    return SKILL.read_text()


def _skill_flat() -> str:
    return re.sub(r"\s+", " ", _skill_text())


def _fake_tmux_runner(calls: list):
    def runner(args, **kwargs):
        calls.append(list(args))

        class R:
            returncode = 0
            stdout = ""
            stderr = ""

        return R()

    return runner


def _git_worktree(tmp_path: Path) -> tuple[Path, str]:
    import subprocess

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


def test_background_tmux_start_is_non_blocking(tmp_path: Path):
    work, head = _git_worktree(tmp_path)
    calls: list = []
    started = start_suite_background(
        worktree=work,
        phase_slug=PHASE,
        phase_head=head,
        log_dir=tmp_path / "logs",
        suite_command="echo ok",
        policy=SuitePolicy(mode="full", command="echo ok", gate="required"),
        runner=_fake_tmux_runner(calls),
    )
    assert isinstance(started, SuiteStart)
    assert started.blocking is False
    assert calls, "tmux must be invoked"
    assert "-d" in calls[0], "tmux session must be detached (non-blocking)"
    assert "new-session" in calls[0]
    assert started.session_name.startswith("orchestra-suite-")
    assert not started.exit_path.exists()


def test_suite_subject_uses_suite_suffix_not_tier2():
    assert suite_subject(PHASE) == f"{PHASE}-suite"
    assert suite_subject(f"{PHASE}-suite") == f"{PHASE}-suite"
    assert suite_subject(f"{PHASE}-tier2") == f"{PHASE}-suite"


def test_runner_records_suite_check_run_payload_fields():
    suite = SuiteResult(
        exit_code=1,
        duration_s=12.5,
        output=(
            "FAILED tests/test_foo.py::test_a\n"
            "FAILED tests/test_bar.py::test_b\n"
        ),
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
    assert payload["runner"] == "aff"
    assert json.loads(payload["failing_node_ids"]) == [
        "tests/test_foo.py::test_a",
        "tests/test_bar.py::test_b",
    ]
    assert payload["criterion_id"] == suite_subject(PHASE)
    assert payload["criterion_id"].endswith("-suite")
    assert not payload["criterion_id"].endswith("-tier2")


def test_tmux_poll_collects_check_run_ready_result(tmp_path: Path):
    import subprocess

    work = tmp_path / "wt"
    work.mkdir()
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    job = SuiteStart(
        session_name="orchestra-suite-demo",
        worktree=work,
        phase_slug="demo",
        phase_head=HEAD,
        log_path=log_dir / "orchestra-suite-demo.log",
        exit_path=log_dir / "orchestra-suite-demo.exit",
        started_monotonic=0.0,
        blocking=False,
    )
    assert poll_suite(job) is None
    job.log_path.write_text("1 passed\n")
    job.exit_path.write_text("0\n")
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
    (work / "f").write_text("1\n")
    subprocess.run(["git", "add", "f"], cwd=work, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "c"],
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
    job.phase_head = head
    result = poll_suite(job)
    assert result is not None
    assert result.exit_code == 0
    assert result.result == "pass"
    assert result.revision == head
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
        phase_slug=PHASE, effort="workflow-loop", suite=suite,
    )
    assert "failing_node_ids" in payload
    assert payload["evidence_kind"] == "integration"
    assert "output_sha256" in payload


def test_phase_gate_required_blocks_on_missing_or_failing_suite():
    acc_a = {"id": "acc-a", "lifecycle_state": "active"}
    acc_b = {"id": "acc-b", "lifecycle_state": "active"}
    policy = SuitePolicy(mode="full", command="pytest", gate="required")
    runs_ok = [
        {
            "criterion_id": "acc-a",
            "revision": HEAD,
            "result": "pass",
            "method": "tdd",
            "runner": "aff",
        },
        {
            "criterion_id": "acc-b",
            "revision": HEAD,
            "result": "pass",
            "method": "check",
            "runner": "aff",
        },
        {
            "subject": suite_subject(PHASE),
            "criterion_id": suite_subject(PHASE),
            "revision": HEAD,
            "result": "pass",
            "method": "check",
            "evidence_kind": "integration",
            "runner": "aff",
        },
    ]
    assert (
        phase_suite_gate_holds(
            acceptances=[acc_a, acc_b],
            check_runs=runs_ok,
            phase_head=HEAD,
            phase_slug=PHASE,
            policy=policy,
        )
        is True
    )
    assert (
        phase_suite_gate_holds(
            acceptances=[acc_a, acc_b],
            check_runs=runs_ok[:-1],
            phase_head=HEAD,
            phase_slug=PHASE,
            policy=policy,
        )
        is False
    )
    failing = list(runs_ok)
    failing[-1] = {**failing[-1], "result": "fail"}
    assert (
        phase_suite_gate_holds(
            acceptances=[acc_a, acc_b],
            check_runs=failing,
            phase_head=HEAD,
            phase_slug=PHASE,
            policy=policy,
        )
        is False
    )
    flat = _skill_flat()
    assert "suite" in flat
    assert "phase_gate.suite" in flat or "phase_gate" in flat
    assert "blocks" in flat


def test_advisory_gate_does_not_block_merge_on_suite_fail():
    acc = {"id": "acc-a", "lifecycle_state": "active"}
    policy = SuitePolicy(mode="full", command="pytest", gate="advisory")
    runs = [
        {
            "criterion_id": "acc-a",
            "revision": HEAD,
            "result": "pass",
            "method": "tdd",
            "runner": "aff",
        },
        {
            "subject": suite_subject(PHASE),
            "criterion_id": suite_subject(PHASE),
            "revision": HEAD,
            "result": "fail",
            "method": "check",
            "evidence_kind": "integration",
            "runner": "aff",
        },
    ]
    assert (
        phase_suite_gate_holds(
            acceptances=[acc],
            check_runs=runs,
            phase_head=HEAD,
            phase_slug=PHASE,
            policy=policy,
        )
        is True
    )
    assert policy.advisory is True
    assert policy.blocks_merge is False
    suite = SuiteResult(
        exit_code=1,
        duration_s=1.0,
        output="FAILED tests/x.py::t\n",
        output_sha256="a",
        failing_node_ids=["tests/x.py::t"],
        result="fail",
        revision=HEAD,
    )
    finding = advisory_finding_payload(
        phase_slug=PHASE, effort="workflow-loop", suite=suite,
    )
    assert "advisory" in finding["claim"]
    assert finding["needs"] == "none"
    routed = route_suite_failures(
        suite.failing_node_ids, fix_budget_remaining=3, policy=policy,
    )
    assert sum(routed.create_fix_flags) == 0
    flat = _skill_flat()
    assert "advisory" in flat
    assert "finding" in flat
    assert "fix-task storm" in flat or "fix-task storms" in flat


def test_mode_none_skips_suite_start(tmp_path: Path):
    work, head = _git_worktree(tmp_path)
    calls: list = []
    policy = SuitePolicy(mode="none", command="", gate="required")
    started = start_suite_background(
        worktree=work,
        phase_slug=PHASE,
        phase_head=head,
        policy=policy,
        runner=_fake_tmux_runner(calls),
    )
    assert isinstance(started, SuiteStart)
    assert started.skipped is True
    assert calls == []
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
        calls: list = []
        started = start_suite_background(
            worktree=work,
            phase_slug=PHASE,
            phase_head=head,
            policy=policy,
            runner=_fake_tmux_runner(calls),
        )
        assert isinstance(started, SuiteStart)
        assert started.skipped is True
        assert policy.run_locally is False
        assert calls == []


def test_mode_smoke_and_full_run_contracted_command(tmp_path: Path):
    work, head = _git_worktree(tmp_path)
    for mode in ("smoke", "full"):
        calls: list = []
        policy = SuitePolicy(mode=mode, command="echo suite-cmd", gate="required")
        started = start_suite_background(
            worktree=work,
            phase_slug=PHASE,
            phase_head=head,
            log_dir=tmp_path / f"logs-{mode}",
            policy=policy,
            runner=_fake_tmux_runner(calls),
        )
        assert isinstance(started, SuiteStart)
        assert not started.skipped
        assert calls
        assert "echo suite-cmd" in " ".join(calls[0])


def test_policy_defaults_missing_mode_none_omitted_gate_required():
    assert normalize_suite_policy(None).mode == "none"
    assert normalize_suite_policy({}).mode == "none"
    configured = normalize_suite_policy({"mode": "smoke", "command": "pytest -q"})
    assert configured.gate == "required"
    assert configured.mode == "smoke"
    loaded = load_suite_policy(REPO_ROOT)
    assert loaded.mode == "full"
    assert loaded.gate == "advisory"
    assert "pytest" in loaded.command


def test_this_repo_suite_policy_full_advisory_from_design():
    # R6: this-repo pin is live design; R2: bundled contract stays mode=none.
    design = json.loads(LIVE_DESIGN.read_text())
    suite = design["phase_gate"]["suite"]
    policy = normalize_suite_policy(suite)
    assert policy.mode == "full"
    assert policy.gate == "advisory"
    assert policy.blocks_merge is False
    assert policy.run_locally is True
    bundled = json.loads(CONTRACT.read_text())["phase_gate"]["suite"]
    assert bundled["mode"] == "none"
    assert bundled.get("command", "") == ""


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
        nodes, fix_budget_remaining=1, policy=policy,
    )
    assert routed.reopen_done is False
    assert routed.inline_fix_and_rerun is False
    assert sum(routed.create_fix_flags) == 1
    assert routed.escalate is True
    routed2 = route_suite_failures(
        nodes, fix_budget_remaining=3, policy=policy,
    )
    assert sum(routed2.create_fix_flags) == 2
    assert all(s.startswith("fix-") for s in routed2.fix_subjects)
    assert should_rerun_suite(fix_tasks_created=sum(routed2.create_fix_flags))
    assert not should_rerun_suite(fix_tasks_created=0)
    flat = _skill_flat()
    assert "cluster" in flat or "failing test file" in flat or "module" in flat
    assert "inline" in flat and (
        "fix-and-rerun" in flat or "fix and rerun" in flat
    )
    assert "never reopen" in flat or ("never" in flat and "`done`" in flat)
    assert "retry" in flat and "budget" in flat


def test_execute_phase_documents_suite_policy_after_reviewer_and_check_run():
    text = _skill_text()
    flat = _skill_flat()
    assert "suite" in flat
    assert "phase_gate.suite" in flat or "phase_gate" in flat
    assert "background" in flat or "detached tmux" in flat
    assert "orchestra suite" in text or "start_suite_background" in text
    assert "waive" in flat
    order = text.index("Phase-end order")
    segment = text[order : order + 500]
    assert segment.index("reviewer") < segment.index("suite")
    creates = [
        inv
        for inv in extract_invocations(text)
        if inv["subcommand"] == "create" and inv["type"] == "project:check-run"
    ]
    suite_creates = [
        inv
        for inv in creates
        if "-suite" in (inv.get("subject") or "")
        or "-suite" in (inv.get("raw") or "")
    ]
    assert suite_creates, "execute-phase must document creating a suite check-run"
    raw = suite_creates[0]["raw"]
    assert "evidence_kind" in raw and "integration" in raw
    assert "output_sha256" in raw
    assert "failing_node_ids" in raw
    assert "orphan" in flat or "reattach" in flat
    assert orphan_recovery_hint(
        SuiteStart(
            session_name="orchestra-suite-x",
            worktree=Path("/tmp"),
            phase_slug="x",
            phase_head=HEAD,
            log_path=Path("/tmp/a.log"),
            exit_path=Path("/tmp/a.exit"),
            started_monotonic=0.0,
        )
    )


def test_execute_phase_documents_no_agent_waiver_of_suite_policy():
    flat = _skill_flat()
    assert "not waive" in flat
    assert "phase_gate.suite" in flat or "phase_gate" in flat
    assert "contract" in flat
    # red-first remains tdd-only; suite never red-first
    assert "never red-first" in flat


def test_readme_suite_command_matches_testing_section():
    cmd = readme_suite_command()
    assert '-n 4 -m "not tmux"' in cmd
    assert "-m tmux" in cmd
    readme = README.read_text()
    # README rename may land in suite-docs-tests; command shape is authoritative.
    assert '-n 4 -m "not tmux"' in readme


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
        phase_slug=PHASE, effort="workflow-loop", suite=suite,
    )
    assert payload["evidence_kind"] == "integration"
    assert payload["evidence_kind"] != "regression"
    design = json.loads(CONTRACT.read_text())
    check = next(r for r in design["records"] if r["name"] == "check-run")
    assert "failing_node_ids" in check["optional_payload"]
    assert "integration" in check["payload_enum"]["evidence_kind"]


def test_mode_none_policy_gate_holds_without_suite_check_run():
    acc = {"id": "acc-a", "lifecycle_state": "active"}
    policy = SuitePolicy(mode="none", command="", gate="required")
    runs = [
        {
            "criterion_id": "acc-a",
            "revision": HEAD,
            "result": "pass",
            "method": "check",
            "runner": "aff",
        },
    ]
    assert (
        phase_suite_gate_holds(
            acceptances=[acc],
            check_runs=runs,
            phase_head=HEAD,
            phase_slug=PHASE,
            policy=policy,
        )
        is True
    )


def test_deferred_gate_is_landing_human_stop_not_local_block():
    policy = SuitePolicy(mode="full", command="pytest", gate="deferred")
    assert policy.deferred_landing_stop is True
    assert policy.run_locally is False
    assert policy.blocks_merge is False
    flat = _skill_flat()
    assert "deferred" in flat
    assert "Landing human stop" in flat or "human stop" in flat
