"""Prove rename_type migration from retired backlog records to composer:idea."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from orchestra.canon.backend import open_backend
from orchestra.canon.migrate import apply_steps
from orchestra.canon.project import open_store

REPO_ROOT = Path(__file__).resolve().parents[1]
CANON_CMD = [sys.executable, "-m", "orchestra.canon"]
SCHEMAS = "score,conductor,tuner,composer"


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def make_git_repo() -> Path:
    root = Path(tempfile.mkdtemp(prefix="orchestra-test-"))
    git(root, "init", "-q")
    git(root, "config", "user.email", "test@example.com")
    git(root, "config", "user.name", "test")
    git(root, "commit", "--allow-empty", "-qm", "init")
    return root

_SCORE = "score"
_COMPOSER = "composer"
_BACKLOG = "backlog" + "-" + "item"
_LEGACY_TYPE = f"{_SCORE}:{_BACKLOG}"
_IDEA_TYPE = f"{_COMPOSER}:idea"

_LEGACY_BACKLOG_TYPE = {
    "purpose": "Deferred work parked on an effort until promoted or dismissed",
    "lifecycle": "current",
    "fields": {
        "effort": {"ref": "score:effort"},
        "status": {"enum": ["open", "promoted", "dismissed"]},
        "source": {"type": "string", "optional": True},
        "phase": {"ref": "score:phase", "optional": True},
    },
}


def _schema_env() -> tuple[Path, dict[str, str]]:
    trimmed = Path(tempfile.mkdtemp(prefix="canon-legacy-score-"))
    env = dict(os.environ)
    paths = []
    for source in os.environ["CANON_SCHEMA_PATH"].split(os.pathsep):
        module = json.loads(Path(source).read_text())
        if module.get("namespace") == _SCORE:
            module = dict(module)
            types = dict(module["types"])
            types[_BACKLOG] = _LEGACY_BACKLOG_TYPE
            module["types"] = types
        target = trimmed / Path(source).name
        target.write_text(json.dumps(module))
        paths.append(str(target))
    env["CANON_SCHEMA_PATH"] = os.pathsep.join(paths)
    return trimmed, env


def _cli(root: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess:
    cmd = [*CANON_CMD, "--root", str(root), *args]
    return subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(REPO_ROOT))


def _init_store(env: dict[str, str]) -> Path:
    root = make_git_repo()
    init = _cli(root, env, "init", "--schemas", SCHEMAS)
    assert init.returncode == 0, init.stdout + init.stderr
    return root


def test_rename_backlog_records_to_ideas_preserves_content_and_history():
    _, env = _schema_env()
    root = _init_store(env)
    effort = _cli(
        root,
        env,
        "create",
        "--type",
        "score:effort",
        "--subject",
        "migrate-effort",
        "--payload",
        json.dumps({"goal": "g", "kind": "deliver"}),
    )
    assert effort.returncode == 0, effort.stdout + effort.stderr

    open_payload = json.dumps({"effort": "migrate-effort", "status": "open", "source": "chat"})
    open_item = _cli(
        root,
        env,
        "create",
        "--type",
        _LEGACY_TYPE,
        "--subject",
        "park-one",
        "--body",
        "Parked body",
        "--payload",
        open_payload,
    )
    assert open_item.returncode == 0, open_item.stdout + open_item.stderr
    open_record = json.loads(open_item.stdout)["record"]

    still_open = _cli(
        root,
        env,
        "create",
        "--type",
        _LEGACY_TYPE,
        "--subject",
        "park-two",
        "--payload",
        json.dumps({"effort": "migrate-effort", "status": "open"}),
    )
    assert still_open.returncode == 0, still_open.stdout + still_open.stderr
    second = json.loads(still_open.stdout)["record"]

    supersede_payload = json.dumps({**open_record["payload"], "status": "dismissed"})
    promoted = _cli(
        root,
        env,
        "supersede",
        "--type",
        _LEGACY_TYPE,
        "--id",
        open_record["id"],
        "--expected-revision",
        open_record["revision"],
        "--payload",
        supersede_payload,
    )
    assert promoted.returncode == 0, promoted.stdout + promoted.stderr
    successor = json.loads(promoted.stdout)["record"]

    project = open_store(root)
    store = open_backend(project.store_path)
    before = {
        record["id"]: record
        for record in project.records()
        if record["record_type"] == _LEGACY_TYPE
    }
    assert set(before) == {open_record["id"], successor["id"], second["id"]}

    step = {"rename_type": {_LEGACY_TYPE: _IDEA_TYPE}}
    rewritten = apply_steps(store, [step])
    assert rewritten == 3

    project = open_store(root)
    store = open_backend(project.store_path)
    ideas = {record["id"]: record for record in project.records() if record["record_type"] == _IDEA_TYPE}
    assert set(ideas) == set(before)
    for record_id, old in before.items():
        new = ideas[record_id]
        assert new["subject"] == old["subject"]
        assert new.get("body") == old.get("body")
        assert new["payload"] == old["payload"]

    assert ideas[successor["id"]]["payload"]["status"] == "dismissed"
    assert ideas[second["id"]]["payload"]["status"] == "open"
    assert ideas[open_record["id"]]["lifecycle_state"] == "superseded"

    for snapshot in store.read_history():
        if snapshot["id"] not in ideas:
            continue
        assert snapshot["record_type"] == _IDEA_TYPE

    legacy_live = list(store.iter_records(_LEGACY_TYPE))
    assert legacy_live == []
