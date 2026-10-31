"""Oracle tests for the analyze checks (spec-analyze phase), driven through `orchestra analyze`."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import helpers as h
from conftest import REPO_ROOT

ORCHESTRA_CMD = [sys.executable, "-m", "orchestra.cli"]
SLUG = "analyze-phase"
EFFORT = "analyze-effort"

PHASE_BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne"
DESIGN_SECTIONS = (
    "Architecture",
    "Interfaces",
    "Decisions",
    "Invariants",
    "Assumptions",
    "Tradeoffs",
    "Risks",
)
SPEC_TAIL = ("Constraints", "Non-goals", "Invariants")


def _orchestra_env() -> dict[str, str]:
    env = dict(os.environ)
    paths = [str(REPO_ROOT)]
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(paths))
    return env


def run_orchestra(store: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*ORCHESTRA_CMD, *args],
        capture_output=True,
        text=True,
        cwd=str(store),
        env=_orchestra_env(),
    )


def run_analyze(store: Path, *args: str, slug: str = SLUG) -> subprocess.CompletedProcess[str]:
    return run_orchestra(store, "analyze", slug, *args)


def analyze_json(store: Path, *args: str, slug: str = SLUG) -> tuple[int, dict]:
    result = run_analyze(store, "--json", *args, slug=slug)
    assert result.stdout.strip(), result.stdout + result.stderr
    return result.returncode, json.loads(result.stdout)


def codes(report: dict, severity: str | None = None) -> set[str]:
    return {f["code"] for f in report["findings"] if severity is None or f["severity"] == severity}


def _create(cli, record_type: str, subject: str, payload: dict, body: str | None = None) -> dict:
    args = ["create", "--type", record_type, "--subject", subject, "--payload", json.dumps(payload)]
    if body is not None:
        args.extend(["--body", body])
    result = cli(*args)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)["record"]


def spec_body(body_ids, *, texts: dict[str, str] | None = None, assumptions: str = "none") -> str:
    texts = texts or {}
    lines = "\n".join(f"{i}: {texts.get(i, 'Behave as stated')}" for i in body_ids)
    return (
        f"## Requirements\n\n{lines}\n\n## Acceptance criteria\n\nSee acceptance records\n\n"
        + "\n\n".join(f"## {name}\n\nnone" for name in SPEC_TAIL)
        + f"\n\n## Assumptions\n\n{assumptions}"
    )


def design_body(*, risks: str = "none") -> str:
    return "\n\n".join(
        f"## {name}\n\n{risks if name == 'Risks' else 'none'}" for name in DESIGN_SECTIONS
    )


def seed_phase(
    cli,
    resolved_contract,
    *,
    ids=("R1", "R2"),
    body_ids=None,
    item_ids=None,
    acceptance_ids=None,
    texts: dict[str, str] | None = None,
    spec_assumptions: str = "none",
    design_risks: str = "none",
    with_spec: bool = True,
    with_design: bool = True,
    slug: str = SLUG,
) -> dict:
    body_ids = ids if body_ids is None else body_ids
    item_ids = ids if item_ids is None else item_ids
    acceptance_ids = ids if acceptance_ids is None else acceptance_ids
    defs = h.record_defs_by_id(resolved_contract)
    h.create_generic_record(cli, defs, "score:effort", subject=EFFORT)
    _create(cli, "score:phase", slug, {"title": slug, "ordinal": 1, "effort": EFFORT}, PHASE_BODY)
    if with_spec:
        _create(
            cli,
            "score:specification",
            f"{slug}-spec",
            {"weight": "full", "phase": slug, "effort": EFFORT, "requirements": list(ids)},
            spec_body(body_ids, texts=texts, assumptions=spec_assumptions),
        )
    if with_design:
        _create(
            cli,
            "score:design",
            f"{slug}-design",
            {"phase": slug, "effort": EFFORT, "decisions": []},
            design_body(risks=design_risks),
        )
    items = {}
    for rid in item_ids:
        items[rid] = _create(
            cli,
            "score:work-item",
            f"{slug}-wi-{rid.lower()}",
            {
                "title": f"item {rid}",
                "phase": slug,
                "kind": "code",
                "assignee": "agent",
                "effort": EFFORT,
                "requirements": [rid],
            },
            "## Description\n\nd",
        )
    acceptances = {}
    for rid in acceptance_ids:
        acceptances[rid] = _create(
            cli,
            "score:acceptance",
            f"{slug}-ac-{rid.lower()}",
            {
                "criterion": f"criterion {rid}",
                "method": "check",
                "phase": slug,
                "effort": EFFORT,
                "verify_command": "true",
                "requirement": rid,
            },
        )
    return {"items": items, "acceptances": acceptances}


def withdraw(cli, record: dict) -> None:
    result = cli(
        "update",
        "--type",
        "score:work-item",
        "--id",
        record["id"],
        "--transition",
        "withdrawn",
        "--expected-revision",
        record["revision"],
    )
    assert result.returncode == 0, result.stdout + result.stderr


def add_check_run(
    store: Path, cli, acceptance: dict, result: str, *, earlier: bool = False
) -> dict:
    payload = {
        "criterion_id": acceptance["id"],
        "revision": "deadbeef",
        "result": result,
        "effort": EFFORT,
        "method": "check",
        "signed_by": "",
        "informed_by": [acceptance["id"]],
    }
    if earlier:
        return h.run_cli_48h_ago(
            store,
            "create",
            "--type",
            "tuner:check-run",
            "--subject",
            acceptance["subject"],
            "--payload",
            json.dumps(payload),
        )
    return _create(cli, "tuner:check-run", acceptance["subject"], payload)


def test_r7_phase_without_specification_exits_zero_and_says_skipped(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, with_spec=False)
    result = run_analyze(store)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "skipped" in (result.stdout + result.stderr)


def test_r8_spec_id_missing_from_body_is_error(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, ids=("R1", "R2", "R3"), body_ids=("R1", "R2"))
    code, report = analyze_json(store)
    assert code == 1
    assert codes(report, "error") == {"spec-id-not-in-body"}
    assert any("R3" in json.dumps(f) for f in report["findings"])


def test_r9_body_id_missing_from_spec_is_error(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, ids=("R1", "R2"), body_ids=("R1", "R2", "R3"))
    code, report = analyze_json(store)
    assert code == 1
    assert codes(report, "error") == {"body-id-not-in-spec"}
    assert any("R3" in json.dumps(f) for f in report["findings"])


def test_r10_requirement_without_work_item_is_error(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, item_ids=("R1",))
    code, report = analyze_json(store)
    assert code == 1
    assert codes(report, "error") == {"requirement-no-work-item"}
    assert any("R2" in json.dumps(f) for f in report["findings"])


def test_r10_withdrawn_work_item_does_not_carry_requirement(store, cli, resolved_contract):
    seeded = seed_phase(cli, resolved_contract)
    withdraw(cli, seeded["items"]["R2"])
    code, report = analyze_json(store)
    assert code == 1
    assert codes(report, "error") == {"requirement-no-work-item"}


def test_r11_requirement_without_acceptance_is_error(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, acceptance_ids=("R1",))
    code, report = analyze_json(store)
    assert code == 1
    assert codes(report, "error") == {"requirement-no-acceptance"}
    assert any("R2" in json.dumps(f) for f in report["findings"])


def test_r12_work_item_with_unlisted_requirement_is_error(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, item_ids=("R1", "R2", "R9"))
    code, report = analyze_json(store)
    assert code == 1
    assert codes(report, "error") == {"work-item-unknown-requirement"}
    assert any("R9" in json.dumps(f) for f in report["findings"])


def test_r12_withdrawn_work_item_with_unlisted_requirement_is_ignored(
    store, cli, resolved_contract
):
    seeded = seed_phase(cli, resolved_contract, item_ids=("R1", "R2", "R9"))
    withdraw(cli, seeded["items"]["R9"])
    code, report = analyze_json(store)
    assert code == 0, report
    assert report["findings"] == []


def test_r13_acceptance_with_unlisted_requirement_is_error(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, acceptance_ids=("R1", "R2", "R9"))
    code, report = analyze_json(store)
    assert code == 1
    assert codes(report, "error") == {"acceptance-unknown-requirement"}
    assert any("R9" in json.dumps(f) for f in report["findings"])


def test_r14_clarification_marker_in_specification_is_error(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, spec_assumptions="[NEEDS CLARIFICATION: which format?]")
    code, report = analyze_json(store)
    assert code == 1
    assert codes(report, "error") == {"clarification-marker"}


def test_r15_clarification_marker_in_design_is_error(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, design_risks="[NEEDS CLARIFICATION: which store?]")
    code, report = analyze_json(store)
    assert code == 1
    assert codes(report, "error") == {"clarification-marker"}


def test_r16_compound_requirement_with_and_is_warning_only(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, texts={"R1": "Read the file and write the report"})
    code, report = analyze_json(store)
    assert code == 0, report
    assert codes(report, "warning") == {"compound-requirement"}
    assert codes(report, "error") == set()
    assert any("R1" in json.dumps(f) for f in report["findings"])


def test_r16_compound_requirement_with_semicolon_is_warning_only(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, texts={"R2": "Read the file; write the report"})
    code, report = analyze_json(store)
    assert code == 0, report
    assert codes(report, "warning") == {"compound-requirement"}


def test_r16_warning_is_printed_in_text_output(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, texts={"R1": "Read the file and write the report"})
    result = run_analyze(store)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "compound-requirement" in result.stdout


def test_r17_acceptance_without_check_run_is_error_in_close_stage(store, cli, resolved_contract):
    seeded = seed_phase(cli, resolved_contract)
    add_check_run(store, cli, seeded["acceptances"]["R1"], "pass")
    code, report = analyze_json(store, "--stage", "close")
    assert code == 1
    assert codes(report, "error") == {"acceptance-no-check-run"}
    assert any(
        "R2" in json.dumps(f) or seeded["acceptances"]["R2"]["id"] in json.dumps(f)
        for f in report["findings"]
    )


def test_r18_acceptance_with_failing_latest_check_run_is_error_in_close_stage(
    store, cli, resolved_contract
):
    seeded = seed_phase(cli, resolved_contract)
    add_check_run(store, cli, seeded["acceptances"]["R1"], "pass")
    add_check_run(store, cli, seeded["acceptances"]["R2"], "fail")
    code, report = analyze_json(store, "--stage", "close")
    assert code == 1
    assert codes(report, "error") == {"acceptance-not-passing"}


def test_r18_latest_check_run_decides_a_pass_after_a_fail(store, cli, resolved_contract):
    seeded = seed_phase(cli, resolved_contract)
    add_check_run(store, cli, seeded["acceptances"]["R1"], "pass")
    add_check_run(store, cli, seeded["acceptances"]["R2"], "fail", earlier=True)
    add_check_run(store, cli, seeded["acceptances"]["R2"], "pass")
    code, report = analyze_json(store, "--stage", "close")
    assert code == 0, report
    assert report["findings"] == []


def test_r18_latest_check_run_decides_a_fail_after_a_pass(store, cli, resolved_contract):
    seeded = seed_phase(cli, resolved_contract)
    add_check_run(store, cli, seeded["acceptances"]["R1"], "pass")
    add_check_run(store, cli, seeded["acceptances"]["R2"], "pass", earlier=True)
    add_check_run(store, cli, seeded["acceptances"]["R2"], "fail")
    code, report = analyze_json(store, "--stage", "close")
    assert code == 1
    assert codes(report, "error") == {"acceptance-not-passing"}


def test_r18_blocked_latest_check_run_is_not_passing(store, cli, resolved_contract):
    seeded = seed_phase(cli, resolved_contract)
    add_check_run(store, cli, seeded["acceptances"]["R1"], "pass")
    add_check_run(store, cli, seeded["acceptances"]["R2"], "blocked")
    code, report = analyze_json(store, "--stage", "close")
    assert code == 1
    assert codes(report, "error") == {"acceptance-not-passing"}


def test_r22_clarification_marker_in_code_span_is_not_a_finding(store, cli, resolved_contract):
    seed_phase(
        cli,
        resolved_contract,
        spec_assumptions="The marker is written `[NEEDS CLARIFICATION: <question>]` in bodies",
        design_risks="Use `[NEEDS CLARIFICATION: <question>]` to flag gaps",
    )
    code, report = analyze_json(store)
    assert code == 0, report
    assert report["findings"] == []


def test_r22_marker_outside_code_span_on_same_line_is_still_a_finding(
    store, cli, resolved_contract
):
    seed_phase(
        cli,
        resolved_contract,
        spec_assumptions="Written `[NEEDS CLARIFICATION: a]` here and [NEEDS CLARIFICATION: b] there",
    )
    code, report = analyze_json(store)
    assert code == 1
    assert codes(report, "error") == {"clarification-marker"}
