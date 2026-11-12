from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from evals.seeded_defects.__main__ import main
from orchestra.tools import RunFn

CASES: dict[str, tuple[str, str | None]] = {
    "syn-rev-1": ("synthetic-defect", "reverted-change"),
    "syn-rev-2": ("synthetic-defect", "reverted-change"),
    "syn-test-1": ("synthetic-defect", "removed-test"),
    "real-1": ("real-escape", None),
    "ctl-1": ("control", None),
    "ctl-2": ("control", None),
}
BANNED = (
    "better",
    "worse",
    "regression",
    "improvement",
    "improved",
    "wins",
    "loses",
    "higher",
    "lower",
    "faster",
    "slower",
    "best",
    "winner",
)


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def write_campaign(
    root: Path,
    name: str,
    *,
    model: str = "m",
    prompt_commit: str = "c",
    case_set_hash: str = "h",
    gate: dict[str, bool],
    calls: dict[str, list[tuple[bool, bool, bool]]],
) -> Path:
    campaign = root / name
    write_json(
        campaign / "campaign.json",
        {"model": model, "prompt_commit": prompt_commit, "case_set_hash": case_set_hash},
    )
    for case_id, caught in gate.items():
        write_json(campaign / "gate" / f"{case_id}.json", {"case_id": case_id, "caught": caught})
    for case_id, results in calls.items():
        for index, (verdict, located, alarm) in enumerate(results, start=1):
            write_json(
                campaign / "calls" / f"{case_id}-{index}.json",
                {
                    "case_id": case_id,
                    "call_index": index,
                    "tokens": 10,
                    "incomplete_reason": None,
                    "incomplete": False,
                    "verdict_catch": verdict,
                    "located_catch": located,
                    "false_alarm": alarm,
                },
            )
    return campaign


def write_cases(root: Path) -> Path:
    cases_dir = root / "cases"
    for case_id, (kind, defect_type) in CASES.items():
        meta: dict[str, object] = {"phase": "p", "revision": "r", "kind": kind}
        if defect_type:
            meta["defect_type"] = defect_type
        write_json(cases_dir / case_id / "case.json", meta)
    return cases_dir


T, F = True, False
GATE_A = {"syn-rev-1": T, "syn-rev-2": F, "syn-test-1": T, "real-1": F, "ctl-1": T}
GATE_B = {**GATE_A, "syn-rev-2": T}
CALLS_A: dict[str, list[tuple[bool, bool, bool]]] = {
    "syn-rev-1": [(T, T, F), (T, F, F), (F, F, F)],
    "syn-rev-2": [(F, F, F), (F, F, F)],
    "syn-test-1": [(T, T, F), (T, T, F)],
    "real-1": [(T, T, F), (T, F, F)],
    "ctl-1": [(F, F, T), (F, F, F)],
    "ctl-2": [(F, F, F), (F, F, F)],
}
CALLS_B: dict[str, list[tuple[bool, bool, bool]]] = {
    **CALLS_A,
    "syn-rev-1": [(T, T, F), (T, T, F), (F, F, F)],
    "ctl-1": [(F, F, F), (F, F, F)],
}
DIFFERING = ["syn-rev-1", "syn-rev-2", "ctl-1"]
SAME = ["syn-test-1", "real-1", "ctl-2"]


def compare(tmp_path: Path, a: Path, b: Path) -> int:
    def fail(*_: object, **__: object) -> object:
        raise AssertionError("compare must not call run or confirm")

    run: RunFn = fail  # pyright: ignore[reportAssignmentType]
    return main(
        ["compare", str(a), str(b), "--cases-dir", str(write_cases(tmp_path))],
        run=run,
        confirm=lambda _: False,
    )


def pair(tmp_path: Path, **b_fields: str) -> tuple[Path, Path]:
    a = write_campaign(tmp_path, "a", prompt_commit="commit-aaa", gate=GATE_A, calls=CALLS_A)
    b = write_campaign(
        tmp_path, "b", **{"prompt_commit": "commit-bbb", **b_fields}, gate=GATE_B, calls=CALLS_B
    )
    return a, b


def test_both_values_of_each_rate(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    a, b = pair(tmp_path)
    assert compare(tmp_path, a, b) == 0
    out = capsys.readouterr().out
    assert "commit-aaa" in out
    assert "commit-bbb" in out
    gate_line = next(
        line for line in out.splitlines() if "synthetic-defect" in line and "/" in line
    )
    assert "2/3 (66.7%)" in gate_line
    assert "3/3 (100.0%)" in gate_line
    alarm_line = next(line for line in out.splitlines() if "false-alarm" in line)
    assert "1/4 (25.0%)" in alarm_line
    assert "0/4 (0.0%)" in alarm_line


def test_lists_differing_cases(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    a, b = pair(tmp_path)
    assert compare(tmp_path, a, b) == 0
    out = capsys.readouterr().out
    _, _, listing = out.partition("differ")
    assert listing
    for case_id in DIFFERING:
        assert re.search(rf"^\s*{case_id}\b", listing, re.MULTILINE)
    for case_id in SAME:
        assert not re.search(rf"^\s*{case_id}\b", listing, re.MULTILINE)


def test_no_verdict_words(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    a, b = pair(tmp_path)
    assert compare(tmp_path, a, b) == 0
    out = capsys.readouterr().out
    assert out.strip()
    for word in BANNED:
        assert not re.search(rf"\b{word}\b", out, re.IGNORECASE), word


@pytest.mark.parametrize(
    ("field", "value"), [("model", "other-model"), ("case_set_hash", "other-hash")]
)
def test_refuses_different_model_or_case_set(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], field: str, value: str
) -> None:
    a, b = pair(tmp_path, **{field: value})
    assert compare(tmp_path, a, b) != 0
    captured = capsys.readouterr()
    assert value in captured.err
    assert field.split("_")[0] in captured.err
    assert captured.out == ""
