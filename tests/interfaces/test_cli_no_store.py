"""Component-owned verbs refuse a directory with no store as `store_not_ready`."""

from __future__ import annotations

from pathlib import Path

import pytest
from interfaces_support import invoke

NO_STORE = "No artifact store for"
REFUSAL_CODE = 2
MINIMAL_CONFIG = (
    '[verify.stages]\ntask = ["unit"]\nphase = ["unit"]\nmilestone = ["unit"]\n\n'
    '[verify.unit]\nrunner = ["true", "{tests}", "{report}"]\n'
)

CONDUCTOR_SUITE_GATE = [
    ("gate", "p1"),
    ("analyze", "p1"),
    ("review-brief", "--phase", "p1"),
]

CONDUCTOR_WAVE_TASK = [
    ("wave", "start", "p1"),
    ("wave", "end", "p1"),
    ("wave", "resolve", "p1", "a"),
    ("task", "land", "--evidence", "x", "t"),
]

CONDUCTOR_LAND_CLOSE = [
    ("land", "--phase", "p1"),
    ("close", "--phase", "p1"),
    ("close-batch", "--input", "close-request.json"),
]

CONDUCTOR_WORKFLOW = [
    ("workflow", "preview", "alpha", "p1", "spec"),
    ("workflow", "start", "alpha", "p1", "spec", "--snapshot-token", "x"),
    ("workflow", "status", "r"),
    ("workflow", "next", "r"),
    ("workflow", "brief", "p1", "spec"),
    (
        "workflow",
        "review",
        "p1",
        "spec",
        "--artifact",
        "x",
        "--authority",
        "user-approval",
        "--basis",
        "b",
    ),
    (
        "workflow",
        "amend-check",
        "a",
        "--expected-revision",
        "1",
        "--basis",
        "b",
        "--routine-check",
        "documentation",
    ),
]

LIGHT_COMPONENTS = [
    (("idea", "A thing"), 1),
    (("place", "alpha", "beta"), 1),
    (("effort", "autonomy", "alpha", "gated"), 2),
    (("effort", "autonomy", "--migrate"), 2),
    (("metrics", "phases"), 1),
    (("metrics", "repairs", "--since", "2020-01-01"), 1),
    (("metrics", "compare", "p1"), 1),
]

TUNER_CANON_STAGE = [
    (("check", "--acceptance", "nope"), 4),
    (("store", "path"), 2),
    (("store", "path", "--json"), 2),
    (("store", "scan"), 2),
    (("store", "recover-evidence"), 2),
    (("store", "run", "--", "list", "--type", "score:effort"), 2),
    (("verify", "trail"), 2),
    (("verify", "recheck", "--claim", "X"), 1),
    (
        ("verify", "bind", "--observation", "o", "--claim", "X", "--base", "a", "--head", "b"),
        1,
    ),
    (("verify", "unbind", "--id", "x"), 1),
]

GROUPS = {
    "conductor_suite_gate": CONDUCTOR_SUITE_GATE,
    "conductor_wave_task": CONDUCTOR_WAVE_TASK,
    "conductor_land_close": CONDUCTOR_LAND_CLOSE,
    "conductor_workflow": CONDUCTOR_WORKFLOW,
}

CASES = (
    [
        pytest.param(argv, REFUSAL_CODE, id=f"{group}-{'_'.join(argv).replace('-', '_')}")
        for group, commands in GROUPS.items()
        for argv in commands
    ]
    + [
        pytest.param(argv, code, id=f"light_components-{'_'.join(argv).replace('-', '_')}")
        for argv, code in LIGHT_COMPONENTS
    ]
    + [
        pytest.param(argv, code, id=f"tuner_canon_stage-{'_'.join(argv).replace('-', '_')}")
        for argv, code in TUNER_CANON_STAGE
    ]
)


@pytest.mark.parametrize(("argv", "code"), CASES)
def test_no_store_is_store_not_ready_with_searched_paths(
    argv: tuple[str, ...], code: int, bare_dir: Path
) -> None:
    (bare_dir / "orchestra.toml").write_text(MINIMAL_CONFIG, encoding="utf-8")
    (bare_dir / "close-request.json").write_text("{}", encoding="utf-8")
    result = invoke("orchestra", list(argv), bare_dir)
    text = result.out + result.err
    assert result.code == code, text
    assert NO_STORE in text
    assert "store_not_ready" in text
    assert "searched" in text
    assert str(bare_dir) in text


def test_conductor_workflow_brief_skill_needs_no_store(bare_dir: Path) -> None:
    result = invoke("orchestra", ["workflow", "brief", "--skill", "init"], bare_dir)
    assert result.code == 0, result.err
    assert "store_not_ready" not in result.out + result.err


def test_light_components_sessions_report_needs_no_store(bare_dir: Path) -> None:
    result = invoke("orchestra", ["sessions", "report", str(bare_dir / "none")], bare_dir)
    assert result.code == 0, result.err
    assert "store_not_ready" not in result.out + result.err


def test_light_components_sessions_aggregate_needs_no_store(bare_dir: Path) -> None:
    (bare_dir / "report.jsonl").write_text("", encoding="utf-8")
    result = invoke(
        "orchestra", ["sessions", "aggregate", str(bare_dir / "report.jsonl")], bare_dir
    )
    assert result.code == 0, result.err
    assert "store_not_ready" not in result.out + result.err


@pytest.mark.parametrize(
    "argv",
    [
        ("install", "--list"),
        ("plugins", "list", "--format", "json"),
        ("verify", "runner-template", "unit"),
    ],
    ids=lambda argv: "tuner_canon_stage-" + "_".join(argv).replace("-", "_"),
)
def test_tuner_canon_stage_store_free_verbs_need_no_store(
    argv: tuple[str, ...], bare_dir: Path
) -> None:
    result = invoke("orchestra", list(argv), bare_dir)
    assert result.code == 0, result.err
    assert "store_not_ready" not in result.out + result.err


def test_tuner_canon_stage_store_ensure_creates_the_store_instead_of_refusing(
    bare_dir: Path,
) -> None:
    result = invoke("orchestra", ["store", "ensure"], bare_dir)
    assert result.code == 0, result.err
    assert "store_not_ready" not in result.out + result.err
    assert (bare_dir / ".canon").is_dir()
