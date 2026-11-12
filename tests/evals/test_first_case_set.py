from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

CASES = Path(__file__).resolve().parents[2] / "evals" / "seeded_defects" / "cases"
MAX_DIFF_BYTES = 30000


def _case_files() -> list[Path]:
    return sorted(CASES.glob("*/case.json"))


def _load() -> list[dict[str, object]]:
    loaded: list[dict[str, object]] = []
    for path in _case_files():
        data: object = json.loads(path.read_text())
        assert isinstance(data, dict)
        loaded.append({str(key): value for key, value in data.items()})  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    return loaded


def test_six_of_each_kind_and_type() -> None:
    counts = Counter((case["kind"], case.get("defect_type")) for case in _load())
    assert counts[("synthetic-defect", "reverted-change")] == 6
    assert counts[("synthetic-defect", "removed-test")] == 6
    assert counts[("control", None)] == 6


def test_at_least_six_phases() -> None:
    phases = {case["phase"] for case in _load()}
    assert len(phases) >= 6


def test_source_diff_under_30_kb() -> None:
    cases = _load()
    assert cases
    for case in cases:
        diff_bytes = case["diff_bytes"]
        assert isinstance(diff_bytes, int)
        assert 0 < diff_bytes < MAX_DIFF_BYTES, case["phase"]
