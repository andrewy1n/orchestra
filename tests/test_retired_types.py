"""Score module and repo must not declare the retired backlog record types."""

from __future__ import annotations

import subprocess

from conftest import REPO_ROOT
from orchestra.canon.modules import discover

_SCORE = "score"
_BACKLOG = "backlog" + "-" + "item"
_FEEDBACK = "feed" + "back"
_RETIRED = (
    f"{_SCORE}:{_BACKLOG}",
    f"{_SCORE}:{_FEEDBACK}",
)


def test_score_module_declares_no_retired_types():
    module = discover()[_SCORE].module
    keys = module["types"]
    assert _BACKLOG not in keys
    assert _FEEDBACK not in keys


def test_tracked_files_outside_history_do_not_name_retired_types():
    listed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    hits: list[str] = []
    for rel in listed:
        if rel.startswith("docs/history/") or rel.startswith(".canon/"):
            continue
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for name in _RETIRED:
            if name in text:
                hits.append(f"{rel}: {name}")
    assert hits == []
