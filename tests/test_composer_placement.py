from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from conftest import REPO_ROOT
from fastapi.testclient import TestClient

from dashboard.backend.server.app import create_app
from orchestra.canon.project import open_store

ORCHESTRA_CMD = [sys.executable, "-m", "orchestra.cli"]
PLACEMENT = "composer:placement"


def run_orchestra(store: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    paths = [str(REPO_ROOT)]
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(paths))
    return subprocess.run(
        [*ORCHESTRA_CMD, *args], capture_output=True, text=True, cwd=str(store), env=env
    )


def _output(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def _create_effort(cli, subject: str) -> None:
    result = cli(
        "create",
        "--type",
        "score:effort",
        "--subject",
        subject,
        "--payload",
        json.dumps({"goal": f"Goal of {subject}", "kind": "deliver"}),
    )
    assert result.returncode == 0, _output(result)


def _create_area(cli, subject: str) -> None:
    result = cli(
        "create",
        "--type",
        "composer:area",
        "--subject",
        subject,
        "--payload",
        json.dumps({"title": f"Area {subject}"}),
        "--body",
        "## Scope\n\nScope for testing.",
    )
    assert result.returncode == 0, _output(result)


def _placements(cli, subject: str | None = None, state: str = "active") -> list[dict]:
    args = ["list", "--type", PLACEMENT, "--state", state, "--full"]
    if subject is not None:
        args.extend(["--subject", subject, "--exact-subject"])
    result = cli(*args)
    assert result.returncode == 0, _output(result)
    return json.loads(result.stdout)["records"]


def _store_fingerprint(store: Path) -> str:
    digest = hashlib.sha256()
    canon_dir = store / ".canon"
    for path in sorted(p for p in canon_dir.rglob("*") if p.is_file()):
        digest.update(path.relative_to(canon_dir).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _placed(store: Path, effort: str, area: str) -> subprocess.CompletedProcess[str]:
    result = run_orchestra(store, "place", effort, area)
    assert "invalid choice: 'place'" not in result.stderr, result.stderr
    assert result.returncode == 0, _output(result)
    return result


def test_schema_defines_placement_with_required_area_ref():
    schema = json.loads(
        (REPO_ROOT / "orchestra" / "composer" / "schemas" / "composer.json").read_text()
    )
    assert "placement" in schema["types"]
    area = schema["types"]["placement"]["fields"]["area"]
    assert area["ref"] == "composer:area"
    assert area.get("optional") is not True


def test_place_creates_placement_for_effort(store, cli):
    _create_effort(cli, "alpha")
    _create_area(cli, "billing")
    _placed(store, "alpha", "billing")
    placements = _placements(cli, "alpha")
    assert len(placements) == 1, placements
    assert placements[0]["subject"] == "alpha"
    assert placements[0]["payload"]["area"] == "billing"
    assert placements[0]["lifecycle_state"] == "active"


def test_place_moves_existing_placement(store, cli):
    _create_effort(cli, "alpha")
    _create_area(cli, "billing")
    _create_area(cli, "search")
    _placed(store, "alpha", "billing")
    _placed(store, "alpha", "search")
    superseded = _placements(cli, "alpha", state="superseded")
    assert [record["payload"]["area"] for record in superseded] == ["billing"]


def test_place_leaves_one_active_after_move(store, cli):
    _create_effort(cli, "alpha")
    _create_area(cli, "billing")
    _create_area(cli, "search")
    _placed(store, "alpha", "billing")
    _placed(store, "alpha", "search")
    assert len(_placements(cli, "alpha")) == 1


def test_place_unknown_effort_exits_nonzero(store, cli):
    _create_area(cli, "billing")
    result = run_orchestra(store, "place", "ghost-effort", "billing")
    assert "invalid choice: 'place'" not in result.stderr, result.stderr
    assert result.returncode != 0, _output(result)
    assert "ghost-effort" in _output(result)


def test_place_unknown_area_exits_nonzero(store, cli):
    _create_effort(cli, "alpha")
    result = run_orchestra(store, "place", "alpha", "ghost-area")
    assert "invalid choice: 'place'" not in result.stderr, result.stderr
    assert result.returncode != 0, _output(result)
    assert "ghost-area" in _output(result)


def test_place_unknown_effort_writes_nothing(store, cli):
    _create_area(cli, "billing")
    before = _store_fingerprint(store)
    result = run_orchestra(store, "place", "ghost-effort", "billing")
    assert "invalid choice: 'place'" not in result.stderr, result.stderr
    assert _store_fingerprint(store) == before


def test_place_unknown_area_writes_nothing(store, cli):
    _create_effort(cli, "alpha")
    before = _store_fingerprint(store)
    result = run_orchestra(store, "place", "alpha", "ghost-area")
    assert "invalid choice: 'place'" not in result.stderr, result.stderr
    assert _store_fingerprint(store) == before


def test_validate_passes_with_placements(store, cli):
    _create_effort(cli, "alpha")
    _create_effort(cli, "beta")
    _create_area(cli, "billing")
    _create_area(cli, "search")
    _placed(store, "alpha", "billing")
    _placed(store, "beta", "billing")
    _placed(store, "beta", "search")
    validated = cli("validate")
    assert validated.returncode == 0, _output(validated)
    assert json.loads(validated.stdout)["status"] == "valid"


def test_place_end_to_end_reaches_snapshot(store, cli):
    _create_effort(cli, "alpha")
    _create_effort(cli, "beta")
    _create_area(cli, "billing")
    _placed(store, "alpha", "billing")
    client = TestClient(create_app(open_store(store)), raise_server_exceptions=False)
    response = client.get("/api/snapshot")
    assert response.status_code == 200, response.text
    areas = {row["effort"]: row.get("area") for row in response.json()["efforts"]}
    assert areas == {"alpha": "billing", "beta": ""}
