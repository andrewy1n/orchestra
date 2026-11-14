from __future__ import annotations

from pathlib import Path

import pytest

from orchestra.cli import main
from orchestra.conductor.briefs import render

SKILLS = ("init", "engage", "triage-ideas", "analyze-sessions")
KINDS_AND_FOCUS_SKILLS = ("init", "engage", "triage-ideas")
SECTIONS = Path(render.__file__).parent / "sections"


def _flat(text: str) -> str:
    return " ".join(text.split())


ENSURE_STORE_SENTENCE = "Do not hardcode a plugin directory or a home checkout in a command."
KINDS_AND_FOCUS_SENTENCE = "Focus is a **subject string**, not a record."


def _invoke(root: Path, capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    try:
        code = main(["workflow", *args, "--store", str(root)])
    except SystemExit as exit_:
        code = exit_.code if isinstance(exit_.code, int) else 1
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_section_sentences_exist_in_source_skill_brief() -> None:
    assert ENSURE_STORE_SENTENCE in _flat((SECTIONS / "ensure-store.md").read_text("utf-8"))
    assert KINDS_AND_FOCUS_SENTENCE in _flat((SECTIONS / "kinds-and-focus.md").read_text("utf-8"))


@pytest.mark.parametrize("skill", SKILLS)
def test_skill_brief_prints_for_each_skill(
    skill: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, output, error = _invoke(tmp_path, capsys, "brief", "--skill", skill)

    assert code == 0, error
    assert output.strip()
    assert ENSURE_STORE_SENTENCE in _flat(output)


@pytest.mark.parametrize("skill", KINDS_AND_FOCUS_SKILLS)
def test_skill_brief_includes_kinds_and_focus(
    skill: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, output, error = _invoke(tmp_path, capsys, "brief", "--skill", skill)

    assert code == 0, error
    assert KINDS_AND_FOCUS_SENTENCE in _flat(output)


def test_skill_brief_needs_no_phase_or_step(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, output, error = _invoke(tmp_path, capsys, "brief", "--skill", "init")

    assert code == 0, error
    assert "required" not in error
    assert output.strip()


@pytest.mark.parametrize("skill", ["spec", "nope"])
def test_skill_brief_unknown_name_lists_valid_names(
    skill: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, output, error = _invoke(tmp_path, capsys, "brief", "--skill", skill)

    assert code != 0
    assert output == ""
    for name in SKILLS:
        assert name in error


@pytest.mark.parametrize("skill", SKILLS)
def test_skill_brief_render_matches_cli(
    skill: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, output, error = _invoke(tmp_path, capsys, "brief", "--skill", skill)

    assert code == 0, error
    assert output
    assert render.render_skill_brief(skill) == output.removesuffix("\n")


def test_skill_brief_render_rejects_unknown_name() -> None:
    with pytest.raises(ValueError) as caught:
        render.render_skill_brief("nope")

    for name in SKILLS:
        assert name in str(caught.value)
