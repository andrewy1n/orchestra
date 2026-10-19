"""Host detection, wizard prompts, and installer defaults."""

from __future__ import annotations

from pathlib import Path

from installer.detect import detected_ids, detect_hosts, installed_ids
from installer.matrix import load_matrix

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
