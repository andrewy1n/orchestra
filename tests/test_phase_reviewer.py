"""Phase-end reviewer: brief, parent writes, fix routing, gate, integration."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from conftest import REPO_ROOT
from skill_extraction import extract_invocations

sys.path.insert(0, str(REPO_ROOT))

from orchestra.reviewer import (  # noqa: E402
    build_finding_payload,
    build_review_check_run_payload,
    build_reviewer_brief,
    grade_reviewer_inputs,
    integration_report_body,
    is_fixable_finding_kind,
    parse_reviewer_output,
    phase_review_gate_holds,
    route_review_findings,
    should_rerun_reviewer,
    verdict_to_result,
)

STATUS_TABS_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "status_tabs_spec_gap.json"

SKILL = REPO_ROOT / "skills" / "execute-phase" / "SKILL.md"

# Unique markers so exclusion asserts cannot false-pass on incidental text.
MARKER_EXEC = "UNIQUE_EXEC_REPORT_BODY_xyz789"
MARKER_CHECK = "UNIQUE_CHECK_RUN_OUTPUT_xyz789"
MARKER_ASSESS = "UNIQUE_ASSESSMENT_REASON_xyz789"
MARKER_ASSIGN = "UNIQUE_ASSIGNMENT_NOTES_xyz789"
MARKER_TASK = "Implement the status tabs per description"
MARKER_ACCEPT = "Tabs render Active and Done filters"
MARKER_REQ = "R2 reviewer receives only task descriptions"
MARKER_INVARIANT = "Reviewer writes no store records"
MARKER_DIFF = "diff --git a/dashboard/app.py b/dashboard/app.py"

SAMPLE_PASS = """
verdict: PASS
findings: []
integration:
  interfaces: tabs wired to model filters
  assumptions: Active/Done labels match design
  invariants: reviewer writes no store records — ok
  conflicts:
"""

SAMPLE_NEEDS_WORK = """
verdict: NEEDS_WORK
findings:
  - task: status-tabs
    kind: spec-gap
    expected: Description lists Active, Done, and Archived tabs
    observed: Acceptance and diff only cover Active and Done
    severity: major
  - task: status-tabs
    kind: behavior-bug
    expected: Done filter hides Active rows
    observed: Done filter no-ops
    severity: major
  - task: phase
    kind: invariant-violation
    expected: Single writer remains the parent
    observed: Judgment call on whether docs imply dual writers
    severity: judgment
integration:
  interfaces: partial tab wiring
  assumptions: labels match design
  invariants: single-writer unclear
  conflicts: Archived promised but not delivered
"""


def _skill_text() -> str:
    return SKILL.read_text()


def _skill_flat() -> str:
    return re.sub(r"\s+", " ", _skill_text())


def test_reviewer_brief_excludes_execution_report_check_run_and_assessment():
    records = [
        {
            "record_type": "project:work-item",
            "subject": "status-tabs",
            "title": "status-tabs",
            "body": (
                "## Description\n\n"
                f"{MARKER_TASK}\n\n"
                "## Approach\n\nShip Active and Done tabs."
            ),
        },
        {
            "record_type": "project:acceptance",
            "subject": "status-tabs",
            "title": "status-tabs",
            "body": f"**criterion**: {MARKER_ACCEPT}",
            "criterion": MARKER_ACCEPT,
        },
        {
            "record_type": "project:requirement",
            "subject": "phase-reviewer",
            "title": "R2",
            "body": MARKER_REQ,
        },
        {
            "record_type": "project:design",
            "subject": "phase-reviewer",
            "title": "invariants",
            "body": f"## Invariants\n\n- {MARKER_INVARIANT}",
        },
        {
            "record_type": "project:execution-report",
            "subject": "status-tabs",
            "title": "status-tabs",
            "body": MARKER_EXEC,
        },
        {
            "record_type": "project:check-run",
            "subject": "status-tabs",
            "title": "status-tabs",
            "body": MARKER_CHECK,
            "result": "pass",
        },
        {
            "record_type": "project:assessment",
            "subject": "status-tabs",
            "title": "status-tabs",
            "body": MARKER_ASSESS,
        },
        {
            "record_type": "project:assignment",
            "subject": "status-tabs",
            "title": "status-tabs",
            "body": MARKER_ASSIGN,
        },
    ]

    brief = build_reviewer_brief(
        records=records,
        phase_diff=MARKER_DIFF + "\n+tabs",
        base="main",
        phase_head="abc1234",
    )

    assert MARKER_TASK in brief
    assert MARKER_ACCEPT in brief
    assert MARKER_REQ in brief
    assert MARKER_INVARIANT in brief
    assert MARKER_DIFF in brief
    assert "main..abc1234" in brief or "git diff main..abc1234" in brief

    for marker in (MARKER_EXEC, MARKER_CHECK, MARKER_ASSESS, MARKER_ASSIGN):
        assert marker not in brief, f"excluded content leaked into brief: {marker}"

    lowered = brief.lower()
    for kind in ("execution-report", "check-run", "assessment", "assignment"):
        assert f"## {kind}" not in lowered
        assert f"### {kind}" not in lowered


def test_execute_phase_invokes_reviewer_after_verification_before_merge():
    text = _skill_text()
    flat = _skill_flat()
    assert "se-reviewer" in flat or "reviewer" in flat
    assert "closing verification" in flat or "verification task" in flat
    # Order markers: verification before reviewer before merge/Landing.
    v_idx = flat.lower().find("closing verification")
    if v_idx < 0:
        v_idx = flat.lower().find("verification task succeeds")
    if v_idx < 0:
        v_idx = flat.lower().find("after the closing verification")
    r_idx = flat.lower().find("reviewer")
    m_idx = flat.lower().find("merge")
    assert v_idx >= 0 and r_idx >= 0 and m_idx >= 0
    assert v_idx < r_idx < m_idx or (
        "after" in flat
        and "verification" in flat
        and "reviewer" in flat
        and "before merge" in flat
    )
    assert "writes no store" in flat or "reviewer writes no" in flat
    # Pre-verification integration-report path relocated.
    assert "from the reviewer" in flat or "reviewer `integration`" in flat or (
        "reviewer's" in flat and "integration" in flat
    )
    # Documented create for review check-run.
    creates = [
        inv
        for inv in extract_invocations(text)
        if inv["subcommand"] == "create" and inv["type"] == "project:check-run"
    ]
    assert any(
        (inv.get("payload") or {}).get("method") == "review"
        and (inv.get("payload") or {}).get("evidence_kind") == "review"
        for inv in creates
    ), "execute-phase must parent-create method:review / evidence_kind:review check-run"


def test_parent_write_review_check_run_and_findings():
    parsed = parse_reviewer_output(SAMPLE_NEEDS_WORK)
    assert parsed["verdict"] == "NEEDS_WORK"
    assert verdict_to_result(parsed["verdict"]) == "fail"
    assert verdict_to_result("PASS") == "pass"

    check = build_review_check_run_payload(
        criterion_id="rec-phase-review-accept",
        phase_head="abc1234deadbeef",
        effort="workflow-loop",
        verdict=parsed["verdict"],
    )
    assert check["method"] == "review"
    assert check["evidence_kind"] == "review"
    assert check["revision"] == "abc1234deadbeef"
    assert check["result"] == "fail"
    assert check["effort"] == "workflow-loop"
    assert check["signed_by"] == ""

    pass_check = build_review_check_run_payload(
        criterion_id="rec-phase-review-accept",
        phase_head="abc1234deadbeef",
        effort="workflow-loop",
        verdict="PASS",
    )
    assert pass_check["result"] == "pass"

    findings = parsed["findings"]
    assert len(findings) == 3
    routed = route_review_findings(
        findings,
        fix_budget_remaining=3,
        reviewer_rerun_used=False,
    )
    payloads = []
    for finding, create_fix in zip(findings, routed.create_fix_flags):
        payloads.append(
            build_finding_payload(
                finding,
                effort="workflow-loop",
                fix_task_created=create_fix,
            )
        )
    assert payloads[0]["needs"] == "none"  # fixable + budget → fix task
    assert payloads[1]["needs"] == "none"
    assert payloads[2]["needs"] == "human"  # judgment
    assert all(p["effort"] == "workflow-loop" for p in payloads)
    assert all("claim" in p and "basis" in p for p in payloads)


def test_review_check_result_maps_verdict():
    assert verdict_to_result("PASS") == "pass"
    assert verdict_to_result("NEEDS_WORK") == "fail"
    assert verdict_to_result("needs_work") == "fail"


def test_fix_task_routing_for_fixable_needs_work():
    assert is_fixable_finding_kind("spec-gap")
    assert is_fixable_finding_kind("behavior-bug")
    assert is_fixable_finding_kind("missing-test")
    assert is_fixable_finding_kind("invariant-violation")
    assert not is_fixable_finding_kind("unknown")

    findings = parse_reviewer_output(SAMPLE_NEEDS_WORK)["findings"]
    routed = route_review_findings(
        findings,
        fix_budget_remaining=2,
        reviewer_rerun_used=False,
    )
    assert routed.create_fix_flags == [True, True, False]
    assert routed.fix_subjects[0].startswith("fix-")
    assert routed.escalate is False
    assert routed.reopen_done is False
    assert should_rerun_reviewer(
        fix_tasks_created=sum(routed.create_fix_flags),
        reviewer_rerun_used=False,
    )


def test_rerun_reviewer_once_after_fixes():
    assert should_rerun_reviewer(fix_tasks_created=1, reviewer_rerun_used=False) is True
    assert should_rerun_reviewer(fix_tasks_created=1, reviewer_rerun_used=True) is False
    assert should_rerun_reviewer(fix_tasks_created=0, reviewer_rerun_used=False) is False
    flat = _skill_flat()
    assert "re-run" in flat or "rerun" in flat or "once" in flat and "reviewer" in flat


def test_budget_exhaustion_escalates_without_reopening_done():
    findings = [
        {
            "task": "a",
            "kind": "spec-gap",
            "expected": "x",
            "observed": "y",
            "severity": "major",
        },
        {
            "task": "b",
            "kind": "behavior-bug",
            "expected": "x",
            "observed": "y",
            "severity": "major",
        },
    ]
    routed = route_review_findings(
        findings,
        fix_budget_remaining=0,
        reviewer_rerun_used=False,
    )
    assert routed.create_fix_flags == [False, False]
    assert routed.escalate is True
    assert routed.reopen_done is False
    flat = _skill_flat()
    assert "never reopen" in flat or ("never" in flat and "`done`" in flat)
    assert "budget" in flat


def test_phase_gate_requires_passing_review_check_at_head():
    head = "deadbeef0123456789abcdef0123456789abcdef"
    assert (
        phase_review_gate_holds(
            check_runs=[
                {
                    "method": "review",
                    "evidence_kind": "review",
                    "result": "pass",
                    "revision": head,
                }
            ],
            phase_head=head,
        )
        is True
    )
    assert (
        phase_review_gate_holds(
            check_runs=[
                {
                    "method": "review",
                    "result": "fail",
                    "revision": head,
                }
            ],
            phase_head=head,
        )
        is False
    )
    assert (
        phase_review_gate_holds(
            check_runs=[
                {
                    "method": "review",
                    "result": "pass",
                    "revision": "otherdeadbeef",
                }
            ],
            phase_head=head,
        )
        is False
    )
    assert phase_review_gate_holds(check_runs=[], phase_head=head) is False
    # Prefix match for short SHAs used in docs.
    assert (
        phase_review_gate_holds(
            check_runs=[
                {"method": "review", "result": "pass", "revision": head[:7]},
            ],
            phase_head=head,
        )
        is True
    )
    flat = _skill_flat()
    assert "method: review" in flat or "`method: review`" in flat or 'method":"review"' in flat
    assert "phase head" in flat or "phase-head" in flat


def test_integration_report_body_from_reviewer_section():
    parsed = parse_reviewer_output(SAMPLE_NEEDS_WORK)
    body = integration_report_body(parsed["integration"])
    assert "## Interfaces" in body
    assert "partial tab wiring" in body
    assert "## Assumptions" in body
    assert "## Invariants" in body
    assert "## Conflicts" in body
    assert "Archived promised" in body
    flat = _skill_flat()
    assert "integration" in flat and "reviewer" in flat
    creates = [
        inv
        for inv in extract_invocations(_skill_text())
        if inv["subcommand"] == "create" and inv["type"] == "project:integration-report"
    ]
    assert len(creates) == 1
    raw = creates[0]["raw"]
    assert "## Interfaces" in raw
    assert "reviewer" in _skill_flat()


def test_status_tabs_fixture_yields_needs_work_spec_gap():
    """Dogfood: description lists more UI than acceptance/diff → NEEDS_WORK / spec-gap."""
    fixture = json.loads(STATUS_TABS_FIXTURE.read_text())
    records = fixture["records"]
    phase_diff = fixture["phase_diff"]

    brief = build_reviewer_brief(
        records=records,
        phase_diff=phase_diff,
        base=fixture.get("base", "main"),
        phase_head=fixture.get("phase_head", "HEAD"),
    )
    assert "Active" in brief and "Done" in brief and "Archived" in brief
    assert "UNIQUE_EXEC_SHOULD_NOT_AFFECT_GRADE" not in brief

    graded = grade_reviewer_inputs(records=records, phase_diff=phase_diff)
    assert graded["verdict"] == "NEEDS_WORK"
    kinds = {f.get("kind") for f in graded["findings"]}
    assert "spec-gap" in kinds
    status_findings = [
        f for f in graded["findings"] if f.get("kind") == "spec-gap"
    ]
    assert status_findings
    assert any(
        "Archived" in (f.get("expected") or "")
        or "Archived" in (f.get("observed") or "")
        for f in status_findings
    )
