"""verify-work splits verify from assess and routes the next stage from evidence."""

from __future__ import annotations

import re

import pytest

import helpers as h
from conftest import REPO_ROOT
from skill_extraction import check_skill_text, extract_invocations

SKILLS = REPO_ROOT / "skills"

ROUTES = (
    ("the cause is the task's code", "failed", "implementation", "execute"),
    ("the design cannot satisfy the requirement", "failed", "design", "design"),
    ("no task covers the requirement", "failed", "plan", "plan"),
    ("the requirement is ambiguous or contradicted", "failed", "specification", "specify"),
    ("integration-report `fail`, and a task must change", "failed", "integration", "execute"),
    ("integration-report `fail`, otherwise", "failed", "integration", "integrate"),
    ("the criterion was not exercised", "insufficient", "verification", "verify"),
    ("every check the requirement needs passed", "verified", None, "release"),
)


def _text(name: str) -> str:
    return h.skill_text(name)


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _writes(name: str, record_type: str, subcommands: set[str] | None = None) -> list[dict]:
    wanted = subcommands or {"create", "supersede"}
    return [
        inv
        for inv in extract_invocations(_text(name))
        if inv["subcommand"] in wanted and inv["type"] == record_type and inv["payload"]
    ]


@pytest.fixture()
def contract_indexes(resolved_contract):
    defs = h.record_defs_by_id(resolved_contract)
    return defs, {}


def test_verify_and_assess_are_separate_steps():
    text = _text("verify-work")
    verify_at = text.index("## Verify")
    assess_at = text.index("# Assess (structured work)")
    assert verify_at < assess_at
    flat = _normalized(text)
    assert "Verify asks what happened. Assess asks what that means and what is next." in flat
    assert "A check-run has no `level` and no `next`." in flat
    for result in ("pass", "fail", "blocked", "insufficient"):
        assert f"`{result}`" in flat
    assert "`insufficient` (the criterion was not exercised)" in flat
    assert "Treat a failing concurrency test as proof the design is wrong" in flat
    assert "put that id and an `evidence_kind` from the schema enum on the check-run" in flat

    check_runs = _writes("verify-work", "tuner:check-run", {"create"})
    assert len(check_runs) == 1
    payload = check_runs[0]["payload"]
    assert "level" not in payload
    assert "next" not in payload
    for field in ("criterion_id", "revision", "result", "effort", "method", "signed_by"):
        assert field in payload
    assert payload["method"] == "manual"
    assert "orchestra check" in text


def test_routing_table_chooses_next_from_the_evidence():
    text = _text("verify-work")
    flat = _normalized(text)
    assert (
        "Choose the first `next` the evidence supports. Do not send every failure to execute"
        in flat
    )
    for cause, status, level, nxt in ROUTES:
        assert cause in text
        row = next(line for line in text.splitlines() if cause in line and line.startswith("|"))
        assert f"`{status}`" in row
        assert f"`{nxt}`" in row
        if level is None:
            assert "omit" in row
        else:
            assert f"`{level}`" in row
    assert "`next` is `verify`, never `execute`" in flat
    assert "`environment` or `unknown`" in text
    assert "acceptance, integration, unit, property, fuzz, review" in flat

    by_next = {
        (inv["payload"].get("level"), inv["payload"]["next"], inv["payload"]["status"])
        for inv in _writes("verify-work", "conductor:assessment")
    }
    assert ("implementation", "execute", "failed") in by_next
    assert ("design", "design", "failed") in by_next
    assert ("verification", "verify", "insufficient") in by_next
    assert ("environment", "verify", "blocked") in by_next
    assert (None, "release", "verified") in by_next


def test_evidence_escalation_ladder():
    text = _normalized(_text("verify-work"))
    assert "## Evidence escalation" in text
    assert "`implementation` → `design` → `specification`" in text
    assert "say in Reason that the evidence did not increase" in text
    assert "Do not escalate by failure count." in text
    assert "new `evidence_kind`" in text
    assert "narrower failing case" in text
    assert "a cause now named" in text
    assert "previous cause is resolved" in text
    assert "not under a repeated implementation failure" in text
    assert "When `specification` repeats without new evidence" in text
    assert "`needs` `human`" in text

    raised = [
        inv
        for inv in _writes("verify-work", "conductor:assessment", {"supersede"})
        if inv["payload"].get("level") == "design" and inv["payload"]["next"] == "design"
    ]
    assert len(raised) == 1
    assert "The evidence did not increase." in raised[0]["raw"]
    assert "implementation" not in raised[0]["payload"].values()

    questions = _writes("verify-work", "score:continuity-question", {"create"})
    assert len(questions) == 1
    assert questions[0]["payload"]["blocking"] is True
    findings = [
        inv
        for inv in _writes("verify-work", "tuner:finding", {"create"})
        if "specification repeated" in inv["payload"]["claim"]
    ]
    assert len(findings) == 1
    assert findings[0]["payload"]["needs"] == "human"


def test_release_ready_only_when_every_requirement_is_verified():
    text = _text("verify-work")
    flat = _normalized(text)
    assert "## Release" in text
    assert "When every assessment for the phase is `verified`" in flat
    assert "Every specification requirement id must have an active `verified` assessment." in flat
    assert "Do not write `merged`, `deployed`, or any other state." in flat
    assert "Do not deploy." in flat
    releases = _writes("verify-work", "conductor:release", {"create"})
    assert len(releases) == 1
    assert releases[0]["payload"]["state"] == "ready"
    assert set(releases[0]["payload"]) >= {"state", "phase", "effort"}
    for inv in extract_invocations(text):
        if inv["type"] == "conductor:release" and inv["payload"]:
            assert inv["payload"]["state"] == "ready"


def test_two_modes_skip_assessment_and_release():
    text = _normalized(_text("verify-work"))
    assert "No specification for this phase, and incidental work, are **simple**" in text
    assert "pass/fail check-runs only — no assessment or release" in text
    assert "Write assessment or release for incidental / no-specification phases" in text


def test_assessment_examples_carry_required_fields_and_sections():
    for inv in _writes("verify-work", "conductor:assessment"):
        payload = inv["payload"]
        for field in ("requirement", "status", "next", "confidence", "phase", "effort"):
            assert field in payload
        assert "level" not in payload or payload["status"] != "verified"
        if payload["status"] == "verified":
            assert "level" not in payload
            assert payload["confidence"] == "high"
            assert payload["next"] == "release"
        else:
            assert payload["confidence"] == "low"
            assert payload.get("level")
        for section in ("## Evidence", "## Missing", "## Reason"):
            assert section in inv["raw"]


def test_engage_does_not_name_score_feedback():
    text = _text("engage")
    retired = ":".join(("score", "feedback"))
    assert retired not in text


def test_engage_documents_idea_list_create_supersede():
    text = _text("engage")
    assert "composer:idea" in text
    assert "**Park**" in text or "Park" in text
    assert "promoted" in text and "dismissed" in text
    invs = extract_invocations(text)
    idea_lists = [
        inv for inv in invs if inv["subcommand"] == "list" and inv["type"] == "composer:idea"
    ]
    assert len(idea_lists) == 2
    by_subject = {inv["raw"] for inv in idea_lists}
    assert any("payload.status=open" in raw for raw in by_subject)
    assert any(
        "--exact-subject" in raw and "--full" in raw and "<idea-subject>" in raw
        for raw in by_subject
    )
    creates = [
        inv for inv in invs if inv["subcommand"] == "create" and inv["type"] == "composer:idea"
    ]
    assert len(creates) == 1
    assert creates[0]["payload"]["status"] == "open"
    assert creates[0]["payload"]["effort"]
    supersedes = [
        inv for inv in invs if inv["subcommand"] == "supersede" and inv["type"] == "composer:idea"
    ]
    statuses = {inv["payload"]["status"] for inv in supersedes if inv["payload"]}
    assert statuses == {"dismissed"}
    retired = ":".join(("score", "feedback"))
    assert retired not in text


def test_engage_idea_input():
    text = _text("engage")
    flat = _normalized(text)
    assert "triaged `composer:idea` subject" in flat
    assert "names the subject of an open" in flat
    assert "start from an idea" in flat
    assert "orchestra view roadmap" in text
    assert "grouped by area" in flat
    assert "--exact-subject" in text
    assert "payload.status" in text and "not `open`" in flat
    assert "payload.effort" in text
    assert "settle-phase" in text and "phase: new" in text
    assert "route to `init`" in flat or "routes to `init`" in flat
    assert "idea: <subject> | none" in text
    assert "Promote an idea from engage" in text
    assert "stays `open` until" in flat
    assert "stops before an effort or phase exists" in flat
    idea_reads = [
        inv
        for inv in extract_invocations(text)
        if inv["subcommand"] == "list"
        and inv["type"] == "composer:idea"
        and "--exact-subject" in inv["raw"]
    ]
    assert len(idea_reads) == 1
    assert idea_reads[0]["type"] == "composer:idea"


def test_verify_work_documents_enforced_red_first_close():
    """R6: verify-work must describe close_batch red-first, not deny it."""
    text = _text("verify-work")
    flat = _normalized(text)
    assert "the engine does not enforce" not in flat
    assert "does not enforce" not in flat
    assert "instruction-level" not in flat
    assert "Nothing in the contract checks" not in text
    assert "red_check_run_id" in text
    assert "red_result" in text
    assert "red_revision" in text
    assert "red_runner" in text
    assert "red_diff_sha256" in text
    assert "enforced" in flat and "red-first" in flat
    assert "pass-only" in flat
    assert "--cwd" in text
    assert '"revision": "<green-sha>"' in text


@pytest.mark.parametrize("skill_name", ["verify-work", "engage"])
def test_documented_invocations_are_contract_legal(contract_indexes, skill_name):
    defs, bundles_by_id = contract_indexes
    violations = check_skill_text(_text(skill_name), defs)
    assert not violations, "\n".join(violations)


def test_assessment_and_check_run_enums_match_the_contract(contract_indexes):
    defs, _ = contract_indexes
    assessment_enum = defs["conductor:assessment"]["payload_enum"]
    check_enum = defs["tuner:check-run"]["payload_enum"]
    assert check_enum["result"] == ["pass", "fail", "blocked", "insufficient"]
    assert check_enum["method"] == ["tdd", "check", "manual", "review"]
    assert defs["score:acceptance"]["payload_enum"]["method"] == [
        "tdd",
        "check",
        "manual",
    ]
    evidence_kinds = set(check_enum["evidence_kind"])
    results = set(check_enum["result"])
    methods = set(check_enum["method"])
    for inv in _writes("verify-work", "tuner:check-run", {"create"}):
        kind = inv["payload"].get("evidence_kind")
        if kind is not None:
            assert kind in evidence_kinds
        assert inv["payload"]["result"] in results
        assert inv["payload"]["method"] in methods
    for inv in _writes("verify-work", "conductor:assessment"):
        payload = inv["payload"]
        assert payload["status"] in assessment_enum["status"]
        assert payload["next"] in assessment_enum["next"]
        assert payload["confidence"] in assessment_enum["confidence"]
        if "level" in payload:
            assert payload["level"] in assessment_enum["level"]
    release_states = set(defs["conductor:release"]["payload_enum"]["state"])
    for inv in _writes("verify-work", "conductor:release", {"create"}):
        assert inv["payload"]["state"] in release_states
        assert inv["payload"]["state"] == "ready"


def test_engage_idea_path_skips_focus_naming_and_always_promotes_through_init_or_settle_phase():
    text = _text("engage")
    assert "skip this step and use step 4" in text
    assert "Set `idea: <idea-subject>` on the routing line." in text
    assert "reopen it first" in text
    assert "always routes through `settle-phase` with" in text


def test_init_and_settle_phase_promote_only_open_ideas():
    for name in ("init", "settle-phase"):
        assert "Promote only when the idea's `payload.status` is `open`" in _text(name)
