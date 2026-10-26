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

_DEFAULT_CANON_ROOT = Path.home() / "adaptive-artifacts"
CANON_ROOT = Path(os.environ.get("CANON_ROOT", str(_DEFAULT_CANON_ROOT))).expanduser().resolve()
CANON_SRC = CANON_ROOT / "src"
CANON_CMD = [sys.executable, "-m", "canon"]


def _affidavit_root() -> Path:
    if os.environ.get("AFFIDAVIT_ROOT"):
        return Path(os.environ["AFFIDAVIT_ROOT"]).expanduser()
    for base in (Path.home() / "affidavit" / ".worktrees" / "canon", Path.home() / "affidavit"):
        if (base / "affidavit" / "schemas" / "aff.json").is_file():
            return base
    return Path.home() / "affidavit"


AFFIDAVIT_ROOT = _affidavit_root()


def _aff_schema() -> Path:
    return AFFIDAVIT_ROOT / "affidavit" / "schemas" / "aff.json"


def _configure_environment() -> None:
    os.environ["CANON_ROOT"] = str(CANON_ROOT)
    os.environ["AFFIDAVIT_ROOT"] = str(AFFIDAVIT_ROOT)
    paths = [str(CANON_SRC), str(REPO_ROOT)]
    existing = os.environ.get("PYTHONPATH", "")
    if existing:
        paths.append(existing)
    os.environ["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(paths))
    for path in reversed(paths):
        if path not in sys.path:
            sys.path.insert(0, path)
    if not os.environ.get("CANON_SCHEMA_PATH"):
        schemas = REPO_ROOT / "orchestra" / "schemas"
        os.environ["CANON_SCHEMA_PATH"] = os.pathsep.join(
            [str(schemas / "plan.json"), str(schemas / "run.json"), str(_aff_schema())]
        )
    shim_dir = Path(tempfile.mkdtemp(prefix="canon-shim-"))
    shim = shim_dir / "canon"
    shim.write_text(f'#!/bin/sh\nexec "{sys.executable}" -m canon "$@"\n')
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR)
    os.environ["PATH"] = f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
    _SHIM_DIRS.append(shim_dir)


_SHIM_DIRS: list[Path] = []


def pytest_configure(config):
    config.addinivalue_line("markers", "tmux: drives a real tmux server; run serially")
    if not (CANON_SRC / "canon").is_dir():
        raise pytest.UsageError(
            f"canon not found at {CANON_SRC}. Set CANON_ROOT to a canon checkout "
            f"or check one out at {_DEFAULT_CANON_ROOT}."
        )
    _configure_environment()


def pytest_unconfigure(config):
    for directory in _SHIM_DIRS:
        shutil.rmtree(directory, ignore_errors=True)


@pytest.fixture(scope="session", autouse=True)
def _preimport_affidavit_binding():
    """Let binding capture the real run_verdict before any test patches it."""
    root = AFFIDAVIT_ROOT
    if (root / "affidavit" / "__init__.py").is_file() and str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        import affidavit.binding  # noqa: F401
    except ImportError:
        pass


def uv_script_source_ok(script_dir: Path, relative: str) -> bool:
    """True when the uv script's `canon` path source resolves to a canon checkout."""
    pyproject = (script_dir / relative / "pyproject.toml")
    try:
        return 'name = "canon"' in pyproject.resolve().read_text()
    except OSError:
        return False


SKILLS_PENDING = {
    "test_assess_routing.py::test_engage_documents_backlog_item_list_create_supersede",
    "test_assess_routing.py::test_engage_routes_feedback_through_settle_phase",
    "test_retry_loop.py::test_plan_phase_consumes_next_plan",
    "test_settle_phase_skill.py::test_kinds_and_focus_documents_human_dismissible_clears",
    "test_settle_phase_skill.py::test_kinds_documents_milestone_hierarchy",
    "test_settle_phase_skill.py::test_plan_phase_opens_a_blocking_plan_review_question",
    "test_settle_phase_skill.py::test_settle_phase_writes_specification_design_decisions_phase_and_questions",
    "test_verify_authority.py::test_skill_does_not_document_hand_create_for_tdd_or_check_methods",
}


def pytest_collection_modifyitems(items):
    for item in items:
        if f"{item.path.name}::{item.name}" in SKILLS_PENDING:
            item.add_marker(pytest.mark.xfail(strict=False, reason="skills migrate on phase/canon-skills"))
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


SCHEMAS = "plan,run,aff"


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
