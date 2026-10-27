"""Shared fixtures for the orchestra test suite.

Stores are built and driven with the `canon` CLI as a subprocess against
temporary git repositories.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("TEXTUAL_ANIMATIONS", "none")

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent

CANON_CMD = [sys.executable, "-m", "orchestra.canon"]
SCHEMA_FILES = (
    REPO_ROOT / "orchestra" / "score" / "schemas" / "score.json",
    REPO_ROOT / "orchestra" / "conductor" / "schemas" / "conductor.json",
    REPO_ROOT / "orchestra" / "tuner" / "schemas" / "tuner.json",
)


def _configure_environment() -> None:
    paths = [str(REPO_ROOT)]
    existing = os.environ.get("PYTHONPATH", "")
    if existing:
        paths.append(existing)
    os.environ["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(paths))
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    os.environ.setdefault("CANON_SCHEMA_PATH", os.pathsep.join(str(f) for f in SCHEMA_FILES))
    shim_dir = Path(tempfile.mkdtemp(prefix="canon-shim-"))
    shim = shim_dir / "canon"
    shim.write_text(f'#!/bin/sh\nexec "{sys.executable}" -m orchestra.canon "$@"\n')
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR)
    os.environ["PATH"] = f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
    _SHIM_DIRS.append(shim_dir)


_SHIM_DIRS: list[Path] = []


def pytest_configure(config):
    config.addinivalue_line("markers", "tmux: drives a real tmux server; run serially")
    _configure_environment()


def pytest_unconfigure(config):
    for directory in _SHIM_DIRS:
        shutil.rmtree(directory, ignore_errors=True)


@pytest.fixture(scope="session", autouse=True)
def _preimport_tuner_binding():
    """Let binding capture the real run_verdict before any test patches it."""
    import orchestra.tuner.binding  # noqa: F401


def pytest_collection_modifyitems(items):
    for item in items:
        if item.path.name in ("test_tmux_integration.py", "test_e2e_dashboard.py", "test_tmux_entry.py"):
            item.add_marker(pytest.mark.tmux)


def run_cli(*args: str, root: Path | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    cmd = list(CANON_CMD)
    if root is not None:
        cmd.extend(["--root", str(root)])
    cmd.extend(args)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd or REPO_ROOT))


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def make_git_repo() -> Path:
    root = Path(tempfile.mkdtemp(prefix="se-workflow-test-"))
    git(root, "init", "-q")
    git(root, "config", "user.email", "test@example.com")
    git(root, "config", "user.name", "test")
    git(root, "commit", "--allow-empty", "-qm", "init")
    return root


SCHEMAS = "score,conductor,tuner"


def write_config(store: Path) -> Path:
    """A minimal canon store marker, with no schemas."""
    store.mkdir(parents=True, exist_ok=True)
    (store / "config.json").write_text(json.dumps({"format": "canon/1", "schemas": {}, "settings": {}}))
    return store


def resolve_contract(root: Path | None = None) -> dict:
    import helpers as h

    return {"records": list(h.schema_defs().values())}


def build_store(drop: frozenset[str] | set[str] = frozenset()) -> Path:
    """A git repo with a canon store; `drop` names unqualified types left out of the schemas."""
    root = make_git_repo()
    env = dict(os.environ)
    if drop:
        trimmed = Path(tempfile.mkdtemp(prefix="canon-trimmed-"))
        paths = []
        for source in os.environ["CANON_SCHEMA_PATH"].split(os.pathsep):
            module = json.loads(Path(source).read_text())
            module["types"] = {k: v for k, v in module["types"].items() if k not in drop}
            target = trimmed / Path(source).name
            target.write_text(json.dumps(module))
            paths.append(str(target))
        env["CANON_SCHEMA_PATH"] = os.pathsep.join(paths)
    init_result = subprocess.run(
        [*CANON_CMD, "--root", str(root), "init", "--schemas", SCHEMAS],
        capture_output=True, text=True, env=env,
    )
    assert init_result.returncode == 0, init_result.stdout + init_result.stderr
    return root


def copy_store(template: Path) -> Path:
    root = Path(tempfile.mkdtemp(prefix="se-workflow-test-"))
    shutil.copytree(template, root, symlinks=True, dirs_exist_ok=True)
    return root


@pytest.fixture(scope="session")
def store_template():
    root = build_store()
    yield root
    shutil.rmtree(root, ignore_errors=True)


@pytest.fixture(scope="session")
def resolved_contract():
    """The record type definitions of the schema modules, in the legacy contract shape."""
    import helpers as h

    return {"records": list(h.schema_defs().values())}


_STAMPED: dict = {}


def stamped_store(store: Path, name: str, build):
    """Replace `store` with a copy of one seeded once per session by build(root, cli, defs); return build's result."""
    if name not in _STAMPED:
        import helpers as h

        root = build_store()

        def cli(*args):
            return run_cli(*args, root=root)

        _STAMPED[name] = (root, build(root, cli, h.schema_defs()))
    root, extra = _STAMPED[name]
    shutil.rmtree(store)
    shutil.copytree(root, store, symlinks=True)
    return extra


@pytest.fixture(scope="session", autouse=True)
def _drop_stamped_stores():
    yield
    for root, _ in _STAMPED.values():
        shutil.rmtree(root, ignore_errors=True)


@pytest.fixture()
def store(store_template):
    """A fresh, disposable, git-backed artifact store copied from one built once per session."""
    root = copy_store(store_template)
    yield root
    shutil.rmtree(root, ignore_errors=True)


@pytest.fixture()
def cli(store):
    """Bound CLI runner for the `store` fixture's root."""

    def _run(*args: str) -> subprocess.CompletedProcess:
        return run_cli(*args, root=store)

    return _run
