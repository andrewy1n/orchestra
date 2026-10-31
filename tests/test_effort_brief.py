"""The score module declares a `brief` type for deliver efforts, and a 1.0.0 store syncs to it."""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from conftest import CANON_CMD, REPO_ROOT, git, make_git_repo

SCORE_MODULE = REPO_ROOT / "orchestra" / "score" / "schemas" / "score.json"
SECTIONS = ("Problem", "Users", "Success measure", "Non-goals")
EFFORT_PAYLOAD = json.dumps({"goal": "Ship it", "kind": "deliver"})


def _module() -> dict:
    return json.loads(SCORE_MODULE.read_text())


def _canon(root: Path, schema_path: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CANON_SCHEMA_PATH": str(schema_path)}
    return subprocess.run(
        [*CANON_CMD, "--root", str(root), *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=env,
    )


def _output(result: subprocess.CompletedProcess) -> str:
    return result.stdout + result.stderr


def _body(sections=SECTIONS) -> str:
    return "\n\n".join(f"## {name}\n\nText for {name}." for name in sections)


def _create_brief(
    root: Path, subject: str, body: str, effort: str = "alpha"
) -> subprocess.CompletedProcess:
    return _canon(
        root,
        SCORE_MODULE,
        "create",
        "--type",
        "score:brief",
        "--subject",
        subject,
        "--payload",
        json.dumps({"effort": effort}),
        "--body",
        body,
    )


def _store_at(version_1_0_0: bool) -> Path:
    root = make_git_repo()
    schema = SCORE_MODULE
    if version_1_0_0:
        module = copy.deepcopy(_module())
        module["version"] = "1.0.0"
        module["types"].pop("brief", None)
        schema = Path(tempfile.mkdtemp(prefix="score-1-0-0-")) / "score.json"
        schema.write_text(json.dumps(module))
    result = _canon(root, schema, "init", "--schemas", "score")
    assert result.returncode == 0, _output(result)
    created = _canon(
        root,
        schema,
        "create",
        "--type",
        "score:effort",
        "--subject",
        "alpha",
        "--payload",
        EFFORT_PAYLOAD,
    )
    assert created.returncode == 0, _output(created)
    git(root, "add", "-A")
    git(root, "commit", "-qm", "seed")
    if schema != SCORE_MODULE:
        shutil.rmtree(schema.parent, ignore_errors=True)
    return root


@pytest.fixture(scope="module")
def current_store():
    root = _store_at(version_1_0_0=False)
    yield root
    shutil.rmtree(root, ignore_errors=True)


@pytest.fixture()
def synced_store():
    root = _store_at(version_1_0_0=True)
    old = json.loads((root / ".canon" / "schemas" / "score.json").read_text())
    assert old["version"] == "1.0.0"
    assert "brief" not in old["types"]
    sync = _canon(root, SCORE_MODULE, "schemas", "sync")
    yield root, sync
    shutil.rmtree(root, ignore_errors=True)


def _snapshot(root: Path) -> dict:
    return json.loads((root / ".canon" / "schemas" / "score.json").read_text())


def test_r1_module_declares_brief_with_current_lifecycle():
    brief = _module()["types"].get("brief")
    assert brief is not None
    assert brief["lifecycle"] == "current"


def test_r2_brief_requires_an_effort_ref_to_score_effort():
    field = _module()["types"].get("brief", {}).get("fields", {}).get("effort")
    assert field == {"ref": "score:effort"}


@pytest.mark.parametrize("missing", SECTIONS)
def test_r3_missing_section_is_rejected_and_named(current_store, missing):
    accepted = _create_brief(current_store, f"control-{missing.lower().replace(' ', '-')}", _body())
    assert accepted.returncode == 0, _output(accepted)
    sections = [name for name in SECTIONS if name != missing]
    result = _create_brief(current_store, "gap", _body(sections))
    assert result.returncode != 0
    assert missing in _output(result)


def test_r4_brief_with_four_sections_and_valid_effort_is_created(current_store):
    result = _create_brief(current_store, "full", _body())
    assert result.returncode == 0, _output(result)
    record = json.loads(result.stdout)["record"]
    assert record["record_type"] == "score:brief"
    assert record["payload"]["effort"] == "alpha"


def test_r5_module_version_is_1_1_0():
    assert _module()["version"] == "1.1.0"


def test_r6_sync_moves_the_snapshot_to_1_1_0(synced_store):
    root, sync = synced_store
    assert sync.returncode == 0, _output(sync)
    assert _snapshot(root)["version"] == "1.1.0"


def test_r7_sync_moves_the_score_pin_to_1_1_0(synced_store):
    root, sync = synced_store
    assert sync.returncode == 0, _output(sync)
    config = json.loads((root / ".canon" / "config.json").read_text())
    assert config["schemas"]["score"] == "1.1.0"


def test_r8_validate_is_clean_for_a_prior_effort_after_sync(synced_store):
    root, sync = synced_store
    assert sync.returncode == 0, _output(sync)
    assert "brief" in _snapshot(root)["types"]
    result = _canon(root, SCORE_MODULE, "validate")
    assert result.returncode == 0, _output(result)
    assert json.loads(result.stdout)["status"] == "valid"
