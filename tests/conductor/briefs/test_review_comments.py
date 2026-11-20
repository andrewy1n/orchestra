from __future__ import annotations

import json
from pathlib import Path

import pytest
from conductor_support import EFFORT, HEAD, PHASE, PHASE_BODY, Cli, Phase, ready_for_verify, seed

from orchestra.canon.project import open_store
from orchestra.cli import main
from orchestra.conductor import phase_progress, suite
from orchestra.conductor.briefs import render
from orchestra.conductor.workflow import step_stage

SECTIONS = Path(render.__file__).parent / "sections"
VERIFY_SENTENCE = "Parent session writes records."
VALID_SKILLS = ("init", "engage", "triage-ideas", "analyze-sessions", "verify")


def _flat(text: str) -> str:
    return " ".join(text.split())


def _invoke(store: Path, capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    try:
        code = main(["workflow", *args, "--store", str(store)])
    except SystemExit as exit_:
        code = exit_.code if isinstance(exit_.code, int) else 1
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _stage(phase: Phase, step: str = "verify", phase_slug: str = PHASE) -> str | None:
    project = open_store(phase.store)
    return step_stage(project, project.records(), phase_slug, step)


def _suite_reason(phase: Phase) -> str:
    project = open_store(phase.store)
    check_runs = [r for r in project.records() if r["record_type"] == "tuner:check-run"]
    return suite.suite_ready_for_review(
        suite.load_suite_policy(project.project_root),
        check_runs,
        phase_slug=PHASE,
        phase_head=HEAD,
    )


def _start_verify(store: Path, capsys: pytest.CaptureFixture[str]) -> str:
    _, output, _ = _invoke(store, capsys, "preview", EFFORT, PHASE, "verify", "--json")
    token = json.loads(output)["snapshot_token"]
    code, output, error = _invoke(
        store, capsys, "start", EFFORT, PHASE, "verify", "--snapshot-token", token, "--json"
    )
    assert code == 0, output + error
    return str(json.loads(output)["run"]["subject"])


def test_verify_skill_brief_sentence_exists_in_the_verify_mechanics_section() -> None:
    assert VERIFY_SENTENCE in _flat((SECTIONS / "verify-mechanics.md").read_text("utf-8"))


def test_verify_skill_brief_prints_without_a_phase(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, output, error = _invoke(tmp_path, capsys, "brief", "--skill", "verify")

    assert code == 0, error
    assert error == ""
    assert output.strip()
    assert VERIFY_SENTENCE in _flat(output)
    assert "{phase}" not in output


def test_verify_skill_brief_json_prints_skill_and_brief(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, plain, error = _invoke(tmp_path, capsys, "brief", "--skill", "verify")
    assert code == 0, error

    code, output, error = _invoke(tmp_path, capsys, "brief", "--skill", "verify", "--json")

    assert code == 0, error
    parsed = json.loads(output)
    assert set(parsed) == {"skill", "brief"}
    assert parsed["skill"] == "verify"
    assert parsed["brief"] == plain.removesuffix("\n")


def test_verify_skill_brief_unknown_name_lists_verify(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, output, error = _invoke(tmp_path, capsys, "brief", "--skill", "nope")

    assert code == 2
    assert output == ""
    assert "nope" in error
    for name in VALID_SKILLS:
        assert name in error


def test_verify_skill_brief_prints_while_the_phase_verify_step_is_blocked(
    store: Path, cli: Cli, capsys: pytest.CaptureFixture[str]
) -> None:
    phase = seed(store, cli, verification="in_progress")
    ready_for_verify(phase)

    code, output, error = _invoke(store, capsys, "brief", PHASE, "verify")

    assert code == 2
    assert output == ""
    assert "execute prerequisite is incomplete" in error

    code, output, error = _invoke(store, capsys, "brief", "--skill", "verify")

    assert code == 0, error
    assert VERIFY_SENTENCE in _flat(output)


@pytest.fixture
def advisory_phase(store: Path, cli: Cli) -> Phase:
    phase = seed(store, cli, review=False)
    ready_for_verify(phase)
    phase.set_suite_policy("advisory")
    return phase


def test_advisory_suite_stage_is_suite_without_a_suite_check_run(advisory_phase: Phase) -> None:
    assert _stage(advisory_phase) == "suite"
    assert _suite_reason(advisory_phase) != ""


def test_advisory_suite_stage_is_reviewer_after_a_failing_suite_check_run(
    advisory_phase: Phase,
) -> None:
    advisory_phase.suite_run("fail")

    assert _stage(advisory_phase) == "reviewer"
    assert _suite_reason(advisory_phase) == ""


def test_advisory_suite_stage_is_reviewer_after_a_passing_suite_check_run(
    advisory_phase: Phase,
) -> None:
    advisory_phase.suite_run("pass")

    assert _stage(advisory_phase) == "reviewer"
    assert _suite_reason(advisory_phase) == ""


def test_stage_read_failures_raise_from_step_stage(
    store: Path, cli: Cli, monkeypatch: pytest.MonkeyPatch
) -> None:
    phase = seed(store, cli)
    ready_for_verify(phase)

    def unreadable(*args: object, **kwargs: object) -> None:
        raise OSError("review evidence unreadable")

    monkeypatch.setattr(phase_progress, "latest_review", unreadable)

    with pytest.raises(OSError, match="review evidence unreadable"):
        _stage(phase)


def test_stage_read_failures_fail_workflow_brief(
    store: Path, cli: Cli, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    phase = seed(store, cli)
    ready_for_verify(phase)

    def unreadable(*args: object, **kwargs: object) -> None:
        raise OSError("review evidence unreadable")

    monkeypatch.setattr(phase_progress, "latest_review", unreadable)

    code, output, error = _invoke(store, capsys, "brief", PHASE, "verify")

    assert code == 2
    assert output == ""
    assert "review evidence unreadable" in error, error


def test_stage_read_failures_fail_workflow_next(
    store: Path, cli: Cli, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    phase = seed(store, cli)
    ready_for_verify(phase)
    run = _start_verify(store, capsys)

    def unreadable(*args: object, **kwargs: object) -> None:
        raise OSError("review evidence unreadable")

    monkeypatch.setattr(phase_progress, "latest_review", unreadable)

    code, output, error = _invoke(store, capsys, "next", run, "--json")

    assert code == 2
    assert output == ""
    assert "review evidence unreadable" in error, error


def test_stage_read_failures_guard_keeps_none_for_unstaged_states(store: Path, cli: Cli) -> None:
    phase = seed(store, cli)
    phase.create(
        "score:phase",
        "bare-phase",
        {"title": "bare", "ordinal": 2, "effort": EFFORT},
        PHASE_BODY,
    )

    assert _stage(phase, "spec") is None
    assert _stage(phase, "land", "bare-phase") is None
