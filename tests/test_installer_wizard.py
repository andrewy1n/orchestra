"""Host detection, wizard prompts, and installer defaults."""

from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

from installer import wizard as wizard_module
from installer.detect import detected_ids, detect_hosts, installed_ids
from installer.matrix import load_matrix
from installer.model import InstallRequest
from installer.wizard import (
    WizardCancelled,
    WizardSelectionError,
    confirm,
    parse_host_selection,
    prompt_hosts,
    prompt_mode,
    prompt_scope,
    wants_wizard,
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


CANONICAL_AGENT = """---
name: reviewer
description: Fixture reviewer
---
Fixture reviewer body.
"""


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    return project


def _make_source(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    skill = source / "skills" / "init"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: init\ndescription: fixture\n---\n", encoding="utf-8"
    )
    agents = source / "agents"
    agents.mkdir()
    (agents / "reviewer.prompt.md").write_text(CANONICAL_AGENT, encoding="utf-8")
    return source


def _run_install(
    *args: str,
    project: Path,
    source: Path,
    home: Path,
    stdin: str | None = None,
) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(REPO_ROOT), env.get("PYTHONPATH", "")]
    ).strip(os.pathsep)
    env["ORCHESTRA_INSTALL_SOURCE"] = str(source)
    env["HOME"] = str(home)
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "install", *args],
        cwd=str(project),
        env=env,
        capture_output=True,
        text=True,
        input=stdin,
    )


def _markers(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob(".orchestra-install.json"))


def test_tty_launches_wizard(monkeypatch):
    monkeypatch.setattr(wizard_module, "_stdin_isatty", lambda: True)
    monkeypatch.setattr(wizard_module, "_stdout_isatty", lambda: True)
    assert wants_wizard(InstallRequest()) is True

    monkeypatch.setattr(wizard_module, "_stdin_isatty", lambda: False)
    assert wants_wizard(InstallRequest()) is False
    assert wants_wizard(InstallRequest(interactive=True)) is True
    assert wants_wizard(InstallRequest(non_interactive=True)) is False
    assert wants_wizard(InstallRequest(list_only=True)) is False
    assert wants_wizard(InstallRequest(uninstall=True)) is False


def test_plan_confirmation(tmp_path):
    project = _project(tmp_path)
    source = _make_source(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    proc = _run_install(
        "--interactive",
        "--copy",
        "--home",
        str(home),
        project=project,
        source=source,
        home=home,
        stdin="1\n\n\n\n",
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "install claude [copy/project]" in proc.stdout
    assert "Proceed? [Y/n]:" in proc.stdout
    assert (home / ".claude" / "skills" / "init" / "SKILL.md").is_file()
    assert _markers(home) == [home / ".claude" / ".orchestra-install.json"]


def test_decline_writes_nothing(tmp_path):
    project = _project(tmp_path)
    source = _make_source(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    proc = _run_install(
        "--interactive",
        "--copy",
        "--home",
        str(home),
        project=project,
        source=source,
        home=home,
        stdin="1\n\nn\n",
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "cancelled" in proc.stderr
    assert not (home / ".claude").exists()
    assert _markers(home) == []


def test_list_prints_matrix(tmp_path):
    project = _project(tmp_path)
    (project / ".claude").mkdir()
    source = _make_source(tmp_path)
    home = tmp_path / "home"
    (home / ".config" / "opencode").mkdir(parents=True)

    proc = _run_install("--list", project=project, source=source, home=home)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "ID" in proc.stdout
    assert "HOST" in proc.stdout
    assert "PROJECT" in proc.stdout
    assert "GLOBAL" in proc.stdout
    assert "Claude Code" in proc.stdout
    assert "OpenCode" in proc.stdout
    assert "yes" in proc.stdout
    assert not (home / ".claude").exists()
    assert not (home / ".opencode").exists()
    assert _markers(home) == []


def test_scope_flag_global_writes_under_home(tmp_path):
    project = _project(tmp_path)
    source = _make_source(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    proc = _run_install(
        "--only",
        "claude",
        "--scope",
        "global",
        "--copy",
        project=project,
        source=source,
        home=home,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (home / ".claude" / "skills" / "init" / "SKILL.md").is_file()
    assert not (project / ".claude").exists()

    conflict = _run_install(
        "--only",
        "claude",
        "--scope",
        "global",
        "--global",
        project=project,
        source=source,
        home=home,
    )
    assert conflict.returncode == 2
    assert "not allowed" in conflict.stderr


def test_interactive_flag_forces_wizard(tmp_path):
    project = _project(tmp_path)
    source = _make_source(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    proc = _run_install(
        "--interactive",
        "--copy",
        "--home",
        str(home),
        project=project,
        source=source,
        home=home,
        stdin="cursor\n\n\n\n",
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Select hosts" in proc.stdout
    assert (home / ".cursor" / "skills" / "init" / "SKILL.md").is_file()
    assert not (home / ".claude").exists()


def test_non_interactive_uses_detected(tmp_path):
    project = _project(tmp_path)
    (project / ".claude").mkdir()
    source = _make_source(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    proc = _run_install(
        "--yes",
        "--copy",
        project=project,
        source=source,
        home=home,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Select hosts" not in proc.stdout
    assert (project / ".claude" / "skills" / "init" / "SKILL.md").is_file()


def test_no_detection_no_tty(tmp_path):
    project = _project(tmp_path)
    source = _make_source(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    proc = _run_install(project=project, source=source, home=home)
    assert proc.returncode == 2
    assert "no host footprints" in proc.stderr
    assert not (project / ".claude").exists()

    yes = _run_install(
        "--yes", project=project, source=source, home=home
    )
    assert yes.returncode == 2
    assert "no host footprints" in yes.stderr
    assert not (project / ".claude").exists()


def test_home_redirect_never_reads_real_home(tmp_path):
    project = _project(tmp_path)
    source = _make_source(tmp_path)
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    redirect = tmp_path / "redirect"
    redirect.mkdir()

    proc = _run_install(
        "--yes",
        "--home",
        str(redirect),
        project=project,
        source=source,
        home=home,
    )

    assert proc.returncode == 2
    assert "no host footprints" in proc.stderr
    assert not (redirect / ".claude").exists()


def test_explicit_flags(tmp_path):
    project = _project(tmp_path)
    source = _make_source(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    only = _run_install(
        "--only",
        "claude",
        "--copy",
        project=project,
        source=source,
        home=home,
    )
    assert only.returncode == 0, only.stdout + only.stderr
    assert "Select hosts" not in only.stdout
    assert (project / ".claude" / "skills" / "init" / "SKILL.md").is_file()

    every = _run_install(
        "--all",
        "--dry-run",
        project=project,
        source=source,
        home=home,
    )
    assert every.returncode == 0, every.stdout + every.stderr
    assert "Select hosts" not in every.stdout
    assert "install claude" in every.stdout
    assert "install cursor" in every.stdout


def test_dry_run_skips_confirmation(tmp_path):
    project = _project(tmp_path)
    source = _make_source(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    proc = _run_install(
        "--interactive",
        "--dry-run",
        "--copy",
        "--home",
        str(home),
        project=project,
        source=source,
        home=home,
        stdin="1\n\n\n",
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Proceed?" not in proc.stdout
    assert "(dry run; nothing written)" in proc.stdout
    assert not (home / ".claude").exists()
    assert _markers(home) == []


def test_uninstall_never_prompts(tmp_path):
    project = _project(tmp_path)
    source = _make_source(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    installed = _run_install(
        "--only",
        "claude",
        "--copy",
        "--home",
        str(home),
        project=project,
        source=source,
        home=home,
    )
    assert installed.returncode == 0, installed.stdout + installed.stderr

    removed = _run_install(
        "--uninstall",
        "--home",
        str(home),
        project=project,
        source=source,
        home=home,
    )

    assert removed.returncode == 0, removed.stdout + removed.stderr
    assert "Select hosts" not in removed.stdout
    assert "uninstalled claude" in removed.stdout
    assert _markers(home) == []


