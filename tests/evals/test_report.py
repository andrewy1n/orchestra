from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from evals.seeded_defects.report import Rate, ReviewerRates, build_report, compute_report

CASES: dict[str, tuple[str, str | None]] = {
    "syn-rev-1": ("synthetic-defect", "reverted-change"),
    "syn-rev-2": ("synthetic-defect", "reverted-change"),
    "syn-test-1": ("synthetic-defect", "removed-test"),
    "real-1": ("real-escape", None),
    "ctl-1": ("control", None),
    "ctl-2": ("control", None),
}
GATE_CAUGHT = {"syn-rev-1": True, "syn-rev-2": False, "syn-test-1": True, "real-1": False}
CALLS: dict[str, list[tuple[bool, bool]]] = {
    "syn-rev-1": [(True, True), (True, False), (False, False)],
    "syn-rev-2": [(False, False), (False, False), (False, False)],
    "syn-test-1": [(True, True), (True, True)],
    "real-1": [(True, True), (True, False), (True, False)],
}
CONTROL_ALARMS = {"ctl-1": [True, False, False], "ctl-2": [False, False]}


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def write_call(campaign: Path, case_id: str, index: int, **fields: object) -> None:
    call: dict[str, object] = {
        "case_id": case_id,
        "call_index": index,
        "tokens": 10,
        "incomplete_reason": None,
        "incomplete": False,
        "verdict_catch": False,
        "located_catch": False,
        "false_alarm": False,
    }
    call.update(fields)
    write_json(campaign / "calls" / f"{case_id}-{index}.json", call)


def build_fixture(tmp_path: Path, incomplete: int = 0) -> tuple[Path, Path]:
    cases_dir = tmp_path / "cases"
    campaign = tmp_path / "campaign"
    for case_id, (kind, defect_type) in CASES.items():
        meta: dict[str, object] = {"phase": "p", "revision": "r", "kind": kind, "extra": 1}
        if defect_type:
            meta["defect_type"] = defect_type
        write_json(cases_dir / case_id / "case.json", meta)
    write_json(
        campaign / "campaign.json", {"model": "m", "prompt_commit": "c", "case_set_hash": "h"}
    )
    for case_id, caught in GATE_CAUGHT.items():
        write_json(campaign / "gate" / f"{case_id}.json", {"case_id": case_id, "caught": caught})
    write_json(campaign / "gate" / "ctl-1.json", {"case_id": "ctl-1", "caught": True})
    for case_id, results in CALLS.items():
        for index, (verdict, located) in enumerate(results, start=1):
            write_call(campaign, case_id, index, verdict_catch=verdict, located_catch=located)
    for case_id, alarms in CONTROL_ALARMS.items():
        for index, alarm in enumerate(alarms, start=1):
            write_call(campaign, case_id, index, false_alarm=alarm)
    targets = ["syn-test-1", "ctl-2", "syn-rev-2"][:incomplete]
    for case_id in targets:
        write_call(
            campaign,
            case_id,
            9,
            incomplete=True,
            incomplete_reason="unparsable",
            verdict_catch=True,
            located_catch=True,
            false_alarm=True,
        )
    return campaign, cases_dir


def test_gate_catch_rate_by_kind_and_type(tmp_path: Path) -> None:
    report = compute_report(*build_fixture(tmp_path))
    assert report.gate_by_kind == {
        "synthetic-defect": Rate(2, 3),
        "real-escape": Rate(0, 1),
    }
    assert report.gate_by_type == {
        "reverted-change": Rate(1, 2),
        "removed-test": Rate(1, 1),
    }


def test_reviewer_rates_by_kind_and_type(tmp_path: Path) -> None:
    report = compute_report(*build_fixture(tmp_path))
    assert report.reviewer_by_kind == {
        "synthetic-defect": ReviewerRates(Rate(4, 8), Rate(3, 8)),
        "real-escape": ReviewerRates(Rate(3, 3), Rate(1, 3)),
    }
    assert report.reviewer_by_type == {
        "reverted-change": ReviewerRates(Rate(2, 6), Rate(1, 6)),
        "removed-test": ReviewerRates(Rate(2, 2), Rate(2, 2)),
    }


def test_false_alarm_rate(tmp_path: Path) -> None:
    campaign, cases_dir = build_fixture(tmp_path)
    assert compute_report(campaign, cases_dir).false_alarm == Rate(1, 5)
    assert "1/5" in build_report(campaign, cases_dir)


def test_unstable_cases_need_three_complete_calls_that_disagree_on_verdict(
    tmp_path: Path,
) -> None:
    report = compute_report(*build_fixture(tmp_path))
    assert report.unstable_cases == 2


def test_incomplete_count_at_top(tmp_path: Path) -> None:
    text = build_report(*build_fixture(tmp_path / "a", incomplete=3))
    assert text.splitlines()[0] == "incomplete calls: 3"
    assert compute_report(*build_fixture(tmp_path / "b", incomplete=3)).incomplete_calls == 3
    clean = build_report(*build_fixture(tmp_path / "c"))
    assert "incomplete" not in clean.splitlines()[0]


def test_incomplete_calls_never_change_a_rate(tmp_path: Path) -> None:
    base = compute_report(*build_fixture(tmp_path / "a"))
    with_incomplete = compute_report(*build_fixture(tmp_path / "b", incomplete=3))
    assert with_incomplete.incomplete_calls == 3
    assert base.incomplete_calls == 0
    assert with_incomplete == replace(base, incomplete_calls=3)


def test_report_text_is_identical_for_identical_saved_results(tmp_path: Path) -> None:
    first = build_report(*build_fixture(tmp_path / "a"))
    second = build_report(*build_fixture(tmp_path / "b"))
    assert first
    assert first == second
