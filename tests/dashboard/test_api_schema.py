import json
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "api_schema.py"
COMMITTED = REPO_ROOT / "dashboard" / "web" / "ui" / "openapi.json"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=REPO_ROOT, capture_output=True, text=True
    )


def test_committed_openapi_schema_matches_the_live_app():
    result = run("--check")
    assert result.returncode == 0, result.stdout + result.stderr


def test_writing_the_schema_reproduces_the_committed_file(tmp_path):
    target = tmp_path / "openapi.json"
    assert run("--schema", str(target)).returncode == 0
    assert target.read_text() == COMMITTED.read_text()
    assert target.read_text().endswith("\n")


def test_check_names_the_regenerate_command_when_the_schema_is_stale(tmp_path):
    stale = tmp_path / "openapi.json"
    document = json.loads(COMMITTED.read_text())
    document["paths"]["/api/bogus"] = {}
    stale.write_text(json.dumps(document, indent=2) + "\n")
    result = run("--check", "--schema", str(stale))
    assert result.returncode == 1
    assert "python scripts/api_schema.py" in result.stderr


def test_check_fails_when_the_schema_file_is_missing(tmp_path):
    assert run("--check", "--schema", str(tmp_path / "absent.json")).returncode == 1
