"""Host detection, wizard prompts, and installer defaults."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from installer.detect import detected_ids, detect_hosts, installed_ids
from installer.matrix import load_matrix
from installer.wizard import (
    WizardCancelled,
    WizardSelectionError,
    confirm,
    parse_host_selection,
    prompt_hosts,
    prompt_mode,
    prompt_scope,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _statuses(tmp_path: Path):
    project = tmp_path / "project"
    global_home = tmp_path / "home"
    project.mkdir()
    global_home.mkdir()
    return detect_hosts(load_matrix(), project, global_home, REPO_ROOT)


def test_detect_hosts_labels_project_and_global(tmp_path):
    project = tmp_path / "project"
    global_home = tmp_path / "home"
    (project / ".claude").mkdir(parents=True)
    (global_home / ".config" / "opencode").mkdir(parents=True)

    statuses = detect_hosts(load_matrix(), project, global_home, REPO_ROOT)
    by_id = {status.provider.id: status for status in statuses}

    assert by_id["claude"].project is True
    assert by_id["claude"].global_ is False
    assert by_id["opencode"].project is False
    assert by_id["opencode"].global_ is True
    assert detected_ids(statuses) == ("claude", "opencode")


def test_detect_hosts_recognizes_registration_markers(tmp_path):
    project = tmp_path / "project"
    global_home = tmp_path / "home"
    marker_dir = project / ".claude"
    marker_dir.mkdir(parents=True)
    (marker_dir / ".orchestra-install.json").write_text("{}\n", encoding="utf-8")

    statuses = detect_hosts(load_matrix(), project, global_home, REPO_ROOT)
    by_id = {status.provider.id: status for status in statuses}

    assert by_id["claude"].project is True
    assert by_id["claude"].marker_project is True
    assert installed_ids(statuses) == ("claude",)


def test_detect_hosts_empty_when_nothing_exists(tmp_path):
    statuses = _statuses(tmp_path)

    assert detected_ids(statuses) == ()
    assert installed_ids(statuses) == ()


def _input_from(*answers: str):
    values = iter(answers)

    def _input(_prompt: str) -> str:
        try:
            return next(values)
        except StopIteration as exc:
            raise EOFError from exc

    return _input


def test_parse_host_selection_accepts_numbers_ids_ranges(tmp_path):
    statuses = _statuses(tmp_path)
    ids = tuple(status.provider.id for status in statuses)

    assert parse_host_selection("1", statuses) == (ids[0],)
    assert parse_host_selection("claude, 3", statuses) == (ids[0], ids[2])
    assert parse_host_selection("1-2", statuses) == ids[:2]
    assert parse_host_selection("1..2", statuses) == ids[:2]
    assert parse_host_selection("1 3", statuses) == (ids[0], ids[2])
    assert parse_host_selection("1,claude", statuses) == (ids[0],)
    assert parse_host_selection("a", statuses) == ids
    assert parse_host_selection("all", statuses) == ids

    with pytest.raises(WizardCancelled):
        parse_host_selection("q", statuses)
    with pytest.raises(WizardCancelled):
        parse_host_selection("quit", statuses)
    with pytest.raises(WizardSelectionError):
        parse_host_selection("nope", statuses)
    with pytest.raises(WizardSelectionError):
        parse_host_selection("9", statuses)


def test_blank_selection_uses_detected(tmp_path):
    project = tmp_path / "project"
    global_home = tmp_path / "home"
    (project / ".claude").mkdir(parents=True)
    (global_home / ".config" / "opencode").mkdir(parents=True)
    statuses = detect_hosts(load_matrix(), project, global_home, REPO_ROOT)
    output = io.StringIO()

    selected = prompt_hosts(
        statuses,
        ("claude", "opencode"),
        input_fn=_input_from(""),
        output=output,
    )

    assert selected == ("claude", "opencode")
    text = output.getvalue()
    assert "[1] Claude Code (claude)" in text
    assert "project: yes" in text
    assert "global: yes" in text


def test_empty_selection_refuses(tmp_path):
    statuses = _statuses(tmp_path)

    with pytest.raises(WizardSelectionError, match="no hosts detected"):
        prompt_hosts(statuses, (), input_fn=_input_from(""), output=io.StringIO())


def test_prompt_scope_defaults_project(tmp_path):
    project = tmp_path / "project"
    global_home = tmp_path / "home"
    output = io.StringIO()

    assert (
        prompt_scope(
            input_fn=_input_from(""),
            output=output,
            project_base=project,
            global_base=global_home,
        )
        == "project"
    )
    assert f"Base: {project}" in output.getvalue()

    output = io.StringIO()
    assert (
        prompt_scope(
            input_fn=_input_from("g"),
            output=output,
            project_base=project,
            global_base=global_home,
        )
        == "global"
    )
    assert f"Base: {global_home}" in output.getvalue()


def test_prompt_mode_defaults_symlink():
    output = io.StringIO()
    assert prompt_mode(input_fn=_input_from(""), output=output) == "symlink"
    assert "Mode: symlink" in output.getvalue()

    output = io.StringIO()
    assert prompt_mode(input_fn=_input_from("c"), output=output) == "copy"
    assert "Mode: copy" in output.getvalue()


def test_confirm_blank_uses_default_and_accepts_no():
    assert confirm("Proceed?", input_fn=_input_from(""), output=io.StringIO())
    assert not confirm("Proceed?", input_fn=_input_from("n"), output=io.StringIO())

