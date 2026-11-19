from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from canon_support import REPO, create, make_project

from orchestra.canon.project import Project
from orchestra.canon.types import JsonValue, Record

PHASE = "ph"
EFFORT = "ef"
LANDING = "\n\n## Landing\n\nbranch: phase/ph\nbase: main\n"
PHASE_BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne"


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _repo(tmp_path: Path) -> tuple[Project, Path]:
    project = make_project(tmp_path)
    (tmp_path / "base.txt").write_text("base\n")
    _git(tmp_path, "add", "base.txt")
    _git(tmp_path, "commit", "-qm", "base")
    _git(tmp_path, "branch", "-M", "main")
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    create(
        project,
        "score:phase",
        PHASE,
        {"title": "Ph", "ordinal": 1, "effort": EFFORT},
        PHASE_BODY + LANDING,
    )
    _git(tmp_path, "branch", f"phase/{PHASE}", "main")
    (tmp_path / ".worktrees").mkdir(exist_ok=True)
    _git(tmp_path, "worktree", "add", "-q", str(tmp_path / ".worktrees" / PHASE), f"phase/{PHASE}")
    return project, tmp_path


def _item(project: Project, slug: str, **extra: JsonValue) -> Record:
    return create(
        project,
        "score:work-item",
        slug,
        {
            "title": slug,
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "executor": "inline",
            **extra,
        },
        f"## Description\n\nDo {slug}.\n\n## Approach\n\nJust {slug}.",
    )


def _malform(project: Project, record: Record, **payload: JsonValue) -> None:
    store, _ = project._session()
    changed = Record(**record)
    changed["payload"] = {**record["payload"], **payload}
    store.write_record(changed, expected_revision=record["revision"])


def _finish(project: Project, repo: Path, record: Record) -> None:
    for transition in ("in_progress", "done"):
        project.update(record["id"], record_type="score:work-item", transition=transition)
    revision = _git(repo, "rev-parse", f"phase/{PHASE}")
    create(
        project,
        "conductor:execution-report",
        record["subject"],
        {
            "work_item": record["subject"],
            "result": "pass",
            "verdict": "pass",
            "revision": revision,
        },
        f"subject: {record['subject']}\nrevision: {revision}\nkind: deliver\nresult: pass",
    )


def _closing_world(tmp_path: Path, **malformed: JsonValue) -> tuple[Project, Path, Record]:
    project, repo = _repo(tmp_path)
    first = _item(project, "a")
    _finish(project, repo, first)
    closer = _item(project, "verify-ph", depends_on=["a"])
    _malform(project, closer, **malformed)
    return project, repo, closer


def _wave_start(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "wave", "start", PHASE],
        capture_output=True,
        text=True,
        cwd=repo,
        env=dict(os.environ, PYTHONPATH=str(REPO)),
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [("requirements", ["R1", 7]), ("requirements", "R1"), ("effort", 5)],
)
def test_r20_malformed_closing_item_fails_naming_id_and_field_and_writes_nothing(
    tmp_path: Path, field: str, value: JsonValue
) -> None:
    project, repo, closer = _closing_world(tmp_path, **{field: value})
    records_before = project.records()

    result = _wave_start(repo)

    assert result.returncode == 2, result.stderr
    assert closer["id"] in result.stderr
    assert f"'{field}'" in result.stderr
    assert "Traceback" not in result.stderr
    after = project.get(closer["id"])
    assert after["lifecycle_state"] == "planned"
    assert [r["subject"] for r in project.list("conductor:execution-report")] == ["a"]
    assert len(project.records()) == len(records_before)


def test_r20_well_formed_closing_item_still_starts_the_runner(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    first = _item(project, "a")
    _finish(project, repo, first)
    closer = _item(project, "verify-ph", depends_on=["a"], requirements=["R1"])

    result = _wave_start(repo)

    assert result.returncode in (0, 1), result.stderr
    assert "Traceback" not in result.stderr
    assert project.get(closer["id"])["lifecycle_state"] != "planned"
