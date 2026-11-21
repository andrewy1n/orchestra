from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from canon_support import REPO, create, make_project

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, JsonValue, Record


def _orchestra(cwd: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(REPO))
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", *argv],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


def _malform(project: Project, record: Record, **fields: JsonValue) -> Record:
    store, _ = project._session()
    payload = {key: value for key, value in record["payload"].items() if key not in fields}
    payload.update({key: value for key, value in fields.items() if value is not None})
    changed = Record(**record)
    changed["payload"] = payload
    return store.write_record(changed, expected_revision=record["revision"])


def _clean_store(tmp_path: Path) -> Project:
    project = make_project(tmp_path)
    create(project, "score:effort", "ef", {"goal": "g", "kind": "deliver"})
    create(project, "composer:idea", "idea", {"status": "open"})
    create(project, "composer:area", "area", {"title": "Area"})
    create(project, "composer:placement", "ef", {"area": "area"})
    return project


def _findings(result: subprocess.CompletedProcess[str]) -> set[tuple[JsonValue, str, str]]:
    entries: list[JsonObject] = [json.loads(line) for line in result.stdout.splitlines()]
    return {(str(e["record_id"]), str(e["record_type"]), str(e["field"])) for e in entries}


def test_scan_reports_malformed_effort_idea_area_and_placement_records(tmp_path: Path) -> None:
    project = _clean_store(tmp_path)
    effort = _malform(project, project.resolve("score:effort", "ef"), goal=None)
    idea = _malform(project, project.resolve("composer:idea", "idea"), status=None)
    area = _malform(project, project.resolve("composer:area", "area"), title=5)
    placement = _malform(project, project.resolve("composer:placement", "ef"), area=None)

    result = _orchestra(tmp_path, "store", "scan", "--json")

    assert result.returncode == 1, result.stderr
    assert _findings(result) == {
        (effort["id"], "score:effort", "goal"),
        (idea["id"], "composer:idea", "status"),
        (area["id"], "composer:area", "title"),
        (placement["id"], "composer:placement", "area"),
    }


def test_scan_exits_zero_on_clean_effort_idea_area_and_placement_records(tmp_path: Path) -> None:
    _clean_store(tmp_path)

    result = _orchestra(tmp_path, "store", "scan")

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
