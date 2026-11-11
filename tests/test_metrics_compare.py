from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from test_metrics_phases import Clock, _check_run, _landing, _phase, _specification, _world

from orchestra.canon.project import Project
from orchestra.cli import main
from orchestra.metrics.compare import compare_phases, render_text

RANKING_WORDS = re.compile(
    r"\b(better|worse|faster|slower|improved|improvement|regressed|regression|win|wins|lose|loses)\b",
    re.IGNORECASE,
)


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> Clock:
    return Clock(monkeypatch)


def _land(
    project: Project,
    clock: Clock,
    name: str,
    day: int,
    *,
    weight: str | None = "light",
    tasks: int = 1,
    spec_day: int | None = None,
    checks: int = 0,
) -> None:
    clock.at(f"2026-11-{spec_day or 1:02d}T00:00:00+00:00")
    _phase(project, name, "ef", weight=weight, tasks=tasks)
    if spec_day is not None:
        _specification(project, name, "ef")
    for _ in range(checks):
        _check_run(project, name, "ef")
    clock.at(f"2026-11-{day:02d}T00:00:00+00:00")
    _landing(project, name)


def _world_with_boundary(tmp_path: Path, clock: Clock) -> Project:
    project = _world(tmp_path)
    _land(project, clock, "ph-boundary", 10)
    return project


def _column(comparison: dict, side: str, weight: str, column: str) -> dict:
    return comparison["sides"][side]["weights"][weight]["columns"][column]


def test_median_and_sample_size_for_each_side_and_weight(tmp_path: Path, clock: Clock) -> None:
    project = _world_with_boundary(tmp_path, clock)
    _land(project, clock, "b1", 2, weight="light", tasks=1)
    _land(project, clock, "b2", 3, weight="light", tasks=3)
    _land(project, clock, "b3", 4, weight="light", tasks=8)
    _land(project, clock, "b4", 5, weight="full", tasks=4)
    _land(project, clock, "a1", 12, weight="light", tasks=10)
    _land(project, clock, "a2", 13, weight="light", tasks=20)
    comparison = compare_phases(tmp_path, "ph-boundary")
    assert _column(comparison, "before", "light", "tasks") == {"median": 3, "n": 3}
    assert _column(comparison, "before", "full", "tasks") == {"median": 4, "n": 1}
    assert _column(comparison, "after", "light", "tasks") == {"median": 15, "n": 2}
    assert "full" not in comparison["sides"]["after"]["weights"]


def test_median_and_sample_size_exclude_the_boundary_phase(tmp_path: Path, clock: Clock) -> None:
    project = _world_with_boundary(tmp_path, clock)
    _land(project, clock, "b1", 2, tasks=5)
    _land(project, clock, "a1", 12, tasks=7)
    comparison = compare_phases(tmp_path, "ph-boundary")
    assert _column(comparison, "before", "light", "tasks")["n"] == 1
    assert _column(comparison, "after", "light", "tasks")["n"] == 1


def test_median_and_sample_size_leave_null_values_out_of_both(tmp_path: Path, clock: Clock) -> None:
    project = _world_with_boundary(tmp_path, clock)
    _land(project, clock, "b1", 3, spec_day=1)
    _land(project, clock, "b2", 5, spec_day=1)
    _land(project, clock, "b3", 6)
    comparison = compare_phases(tmp_path, "ph-boundary")
    elapsed = _column(comparison, "before", "light", "elapsed_seconds")
    assert elapsed == {"median": 3 * 86400, "n": 2}
    assert _column(comparison, "before", "light", "tasks")["n"] == 3


def test_median_and_sample_size_of_a_column_with_no_values_is_null_and_zero(
    tmp_path: Path, clock: Clock
) -> None:
    project = _world_with_boundary(tmp_path, clock)
    _land(project, clock, "b1", 3)
    comparison = compare_phases(tmp_path, "ph-boundary")
    assert _column(comparison, "before", "light", "elapsed_seconds") == {"median": None, "n": 0}


def test_median_and_sample_size_group_a_phase_without_weight_as_unrecorded(
    tmp_path: Path, clock: Clock
) -> None:
    project = _world_with_boundary(tmp_path, clock)
    _land(project, clock, "b1", 3, weight=None, tasks=6)
    comparison = compare_phases(tmp_path, "ph-boundary")
    assert _column(comparison, "before", "unrecorded", "tasks") == {"median": 6, "n": 1}


def test_median_and_sample_size_count_a_phase_without_landing_time_as_unplaced(
    tmp_path: Path, clock: Clock
) -> None:
    project = _world_with_boundary(tmp_path, clock)
    _land(project, clock, "b1", 3)
    clock.at("2026-11-02T00:00:00+00:00")
    _phase(project, "ph-nolanding", "ef", tasks=1)
    comparison = compare_phases(tmp_path, "ph-boundary")
    assert comparison["unplaced"] == 1
    assert _column(comparison, "before", "light", "tasks")["n"] == 1
    assert "light" not in comparison["sides"]["after"]["weights"]


def test_median_and_sample_size_appear_in_text_output(tmp_path: Path, clock: Clock) -> None:
    project = _world_with_boundary(tmp_path, clock)
    _land(project, clock, "b1", 3, tasks=4)
    text = render_text(compare_phases(tmp_path, "ph-boundary"))
    assert "before" in text and "after" in text
    assert "light" in text and "unplaced" in text
    assert re.search(r"tasks\D+4\D+1", text)


def test_no_verdict_words_in_text_or_json_output(tmp_path: Path, clock: Clock) -> None:
    project = _world_with_boundary(tmp_path, clock)
    _land(project, clock, "b1", 3, tasks=9, spec_day=1)
    _land(project, clock, "a1", 12, tasks=1, spec_day=11)
    _land(project, clock, "a2", 13, weight=None, tasks=2)
    comparison = compare_phases(tmp_path, "ph-boundary")
    for output in (render_text(comparison), json.dumps(comparison)):
        assert RANKING_WORDS.search(output) is None


def test_no_verdict_between_sides_holds_when_one_side_is_clearly_lower(
    tmp_path: Path, clock: Clock
) -> None:
    project = _world_with_boundary(tmp_path, clock)
    _land(project, clock, "b1", 3, tasks=50)
    _land(project, clock, "a1", 12, tasks=1)
    text = render_text(compare_phases(tmp_path, "ph-boundary"))
    assert RANKING_WORDS.search(text) is None
    assert set(compare_phases(tmp_path, "ph-boundary")["sides"]) == {"before", "after"}


def test_cli_prints_a_table_for_each_side(
    tmp_path: Path, clock: Clock, capsys: pytest.CaptureFixture[str]
) -> None:
    project = _world_with_boundary(tmp_path, clock)
    _land(project, clock, "b1", 3, tasks=4)
    assert main(["metrics", "compare", "ph-boundary", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "boundary\tph-boundary" in out
    assert "    tasks\t4\t1" in out
    assert "unplaced\t0" in out


def test_cli_json_matches_the_comparison(
    tmp_path: Path, clock: Clock, capsys: pytest.CaptureFixture[str]
) -> None:
    project = _world_with_boundary(tmp_path, clock)
    _land(project, clock, "b1", 3, tasks=4)
    _land(project, clock, "a1", 12, weight=None, tasks=2)
    assert main(["metrics", "compare", "ph-boundary", "--json", str(tmp_path)]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed == json.loads(json.dumps(compare_phases(tmp_path, "ph-boundary")))
    assert "unrecorded" in printed["sides"]["after"]["weights"]


def test_cli_unknown_boundary_exits_non_zero_with_a_message(
    tmp_path: Path, clock: Clock, capsys: pytest.CaptureFixture[str]
) -> None:
    _world_with_boundary(tmp_path, clock)
    assert main(["metrics", "compare", "ph-missing", str(tmp_path)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "ph-missing" in captured.err


def test_cli_boundary_without_landing_time_exits_non_zero(
    tmp_path: Path, clock: Clock, capsys: pytest.CaptureFixture[str]
) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-nolanding", "ef")
    assert main(["metrics", "compare", "ph-nolanding", str(tmp_path)]) == 1
    assert "landing time" in capsys.readouterr().err
