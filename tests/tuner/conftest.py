"""Shared fixtures: disposable git repos with a canon store (score, conductor, tuner)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("TEXTUAL_ANIMATIONS", "none")

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parents[1]
SCHEMA_FILES = (
    REPO_ROOT / "orchestra" / "score" / "schemas" / "score.json",
    REPO_ROOT / "orchestra" / "conductor" / "schemas" / "conductor.json",
    REPO_ROOT / "orchestra" / "tuner" / "schemas" / "tuner.json",
    REPO_ROOT / "orchestra" / "composer" / "schemas" / "composer.json",
)

def pytest_configure(config):
    config.addinivalue_line("markers", "tmux: drives a real tmux server; run serially")
    root = str(REPO_ROOT)
    paths = [p for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p]
    if root not in paths:
        os.environ["PYTHONPATH"] = os.pathsep.join([root, *paths])
    if root not in sys.path:
        sys.path.insert(0, root)
    os.environ.setdefault("CANON_SCHEMA_PATH", os.pathsep.join(str(f) for f in SCHEMA_FILES))


def run_cli(*args: str, root: Path | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "orchestra.canon"]
    if root is not None:
        cmd.extend(["--root", str(root)])
    cmd.extend(args)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd or REPO_ROOT))


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def make_git_repo() -> Path:
    root = Path(tempfile.mkdtemp(prefix="tuner-test-"))
    git(root, "init", "-q")
    git(root, "config", "user.email", "test@example.com")
    git(root, "config", "user.name", "test")
    git(root, "commit", "--allow-empty", "-qm", "init")
    return root


def build_store() -> Path:
    root = make_git_repo()
    init_result = run_cli("init", "--schemas", "score,conductor,tuner", root=root)
    assert init_result.returncode == 0, init_result.stdout + init_result.stderr
    return root


def copy_store(template: Path) -> Path:
    root = Path(tempfile.mkdtemp(prefix="tuner-test-"))
    shutil.copytree(template, root, symlinks=True, dirs_exist_ok=True)
    return root


@pytest.fixture(scope="session")
def store_template():
    root = build_store()
    yield root
    shutil.rmtree(root, ignore_errors=True)


@pytest.fixture()
def store(store_template):
    """A fresh, disposable, git-backed canon store copied from one built once per session."""
    root = copy_store(store_template)
    yield root
    shutil.rmtree(root, ignore_errors=True)


@pytest.fixture()
def cli(store):
    def _run(*args: str) -> subprocess.CompletedProcess:
        return run_cli(*args, root=store)

    return _run
