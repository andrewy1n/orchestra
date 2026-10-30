"""Oracle tests for the `orchestra analyze` command surface: exit codes, JSON shape, stages."""

from __future__ import annotations

import json

from test_analyze import SLUG, add_check_run, analyze_json, codes, run_analyze, seed_phase

CHECK_RUN_CODES = {"acceptance-no-check-run", "acceptance-not-passing"}


def test_r1_consistent_phase_exits_zero(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract)
    result = run_analyze(store)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "invalid choice" not in result.stderr
    assert result.stdout.strip()


def test_r1_warning_only_phase_exits_zero(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, texts={"R1": "Read the file and write the report"})
    code, report = analyze_json(store)
    assert code == 0, report
    assert report["findings"]


def test_r2_phase_with_an_error_exits_one(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, item_ids=("R1",))
    result = run_analyze(store)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "invalid choice" not in result.stderr
    assert "requirement-no-work-item" in result.stdout


def test_r3_unknown_phase_exits_two_and_names_the_slug_on_stderr(store):
    result = run_analyze(store, slug="ghost-phase")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "ghost-phase" in result.stderr
    assert "invalid choice" not in result.stderr


def test_r3_other_phases_do_not_satisfy_the_lookup(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract)
    result = run_analyze(store, slug="ghost-phase")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "ghost-phase" in result.stderr


def test_r4_json_output_is_one_object_with_phase_stage_and_findings(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, item_ids=("R1",))
    result = run_analyze(store, "--json")
    assert result.returncode == 1, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert isinstance(report, dict)
    assert report["phase"] == SLUG
    assert report["stage"] == "plan"
    assert isinstance(report["findings"], list)


def test_r4_each_finding_carries_severity_code_subject_and_message(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, item_ids=("R1",))
    _, report = analyze_json(store)
    assert report["findings"]
    for finding in report["findings"]:
        assert {"severity", "code", "subject", "message"} <= set(finding)
        assert finding["severity"] in {"error", "warning"}


def test_r4_clean_phase_has_an_empty_findings_list(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract)
    code, report = analyze_json(store)
    assert code == 0
    assert report["findings"] == []
    assert report["phase"] == SLUG


def test_r5_default_stage_is_plan(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract)
    _, report = analyze_json(store)
    assert report["stage"] == "plan"


def test_r5_plan_stage_reports_no_check_run_finding(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract)
    code, report = analyze_json(store)
    assert code == 0, report
    assert codes(report) & CHECK_RUN_CODES == set()
    assert report["stage"] == "plan"


def test_r5_explicit_plan_stage_matches_the_default(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, item_ids=("R1",))
    default = analyze_json(store)
    explicit = analyze_json(store, "--stage", "plan")
    assert default == explicit
    assert explicit[1]["stage"] == "plan"


def test_r6_close_stage_on_consistent_store_with_passing_check_runs_exits_zero(store, cli, resolved_contract):
    seeded = seed_phase(cli, resolved_contract)
    for acceptance in seeded["acceptances"].values():
        add_check_run(store, cli, acceptance, "pass")
    code, report = analyze_json(store, "--stage", "close")
    assert code == 0, report
    assert report["stage"] == "close"
    assert report["findings"] == []


def test_r6_close_stage_runs_plan_checks_and_check_run_checks(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, item_ids=("R1",))
    code, report = analyze_json(store, "--stage", "close")
    assert code == 1
    assert report["stage"] == "close"
    assert {"requirement-no-work-item", "acceptance-no-check-run"} <= codes(report, "error")


def test_r6_plan_stage_on_the_same_store_omits_check_run_checks(store, cli, resolved_contract):
    seed_phase(cli, resolved_contract, item_ids=("R1",))
    _, report = analyze_json(store, "--stage", "plan")
    assert "requirement-no-work-item" in codes(report, "error")
    assert codes(report) & CHECK_RUN_CODES == set()
