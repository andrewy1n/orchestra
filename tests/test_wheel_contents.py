"""Acceptance tests for the wheel-contents phase."""

from __future__ import annotations

import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

_IMPORT_IN_INSTALL = r"""
import site
import sys
from pathlib import Path

sites, module, *banned_args = sys.argv[1:]
banned = {Path(entry).resolve() for entry in banned_args}
for directory in sites.split("|"):
    if directory:
        site.addsitedir(directory)


def _kept(entry: str) -> bool:
    if not entry:
        return True
    try:
        return Path(entry).resolve() not in banned
    except OSError:
        return True


sys.path[:] = [entry for entry in sys.path if _kept(entry)]
if any(entry and Path(entry).resolve() in banned for entry in sys.path):
    sys.stderr.write("repository root is on sys.path\n")
    raise SystemExit(1)
try:
    __import__(module)
except Exception as exc:
    sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
    raise SystemExit(1)
"""

_BLOCKED_CLI_IMPORT = r"""
import importlib.abc
import importlib.machinery
import sys

repo, blocked = sys.argv[1], sys.argv[2]
sys.path.insert(0, repo)
missing = blocked + "._missing"


class _Loader(importlib.abc.Loader):
    def create_module(self, spec):
        return None

    def exec_module(self, module):
        raise ModuleNotFoundError(missing, name=missing)


class _Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == blocked or fullname.startswith(blocked + "."):
            return importlib.machinery.ModuleSpec(fullname, _Loader(), is_package=False)
        return None


sys.meta_path.insert(0, _Finder())
try:
    import orchestra.cli
except ModuleNotFoundError as exc:
    name = exc.name or ""
    if name == blocked or name.startswith(blocked + "."):
        raise SystemExit(0)
    sys.stderr.write(f"ModuleNotFoundError name {name!r}\n")
    raise SystemExit(1)
except Exception as exc:
    sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
    raise SystemExit(1)
else:
    sys.stderr.write("import succeeded\n")
    raise SystemExit(1)
"""

_EFFORT_ROLLUP = r"""
import sys
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
scripts = (repo / "scripts").resolve()
sys.path.insert(0, str(repo))
sys.path[:] = [
    entry for entry in sys.path if not entry or Path(entry).resolve() != scripts
]
before = list(sys.path)
try:
    from orchestra.score import effort_rollup
except Exception as exc:
    sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
    raise SystemExit(1)
else:
    del effort_rollup
for entry in sys.path:
    if entry and entry not in before and Path(entry).resolve() == scripts:
        sys.stderr.write(f"inserted {entry}\n")
        raise SystemExit(1)
"""

_NO_SYSPATH_INSERT = r"""
import os
import sys
import tempfile
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
attr = sys.argv[2]
os.environ.pop("ORCHESTRA_SCRIPTS", None)
sys.path.insert(0, str(repo))
import orchestra.sessions as sessions

root = Path(tempfile.mkdtemp())
before = list(sys.path)
exercised = False
try:
    __import__(f"orchestra.sessions.{attr}")
    exercised = True
except ModuleNotFoundError:
    pass
call = getattr(sessions, attr, None)
if callable(call):
    exercised = True
    target = root / "report.jsonl"
    target.write_text("")
    try:
        call(root if attr == "report" else target)
    except Exception:
        pass
inserted = [
    entry
    for entry in sys.path
    if entry not in before and entry and Path(entry).is_dir()
]
if not exercised:
    sys.stderr.write(f"orchestra.sessions.{attr} is missing\n")
    raise SystemExit(1)
if inserted:
    sys.stderr.write("inserted " + inserted[0] + "\n")
    raise SystemExit(1)
"""

_PROVIDERS_JSON = r"""
import site
import sys
from pathlib import Path

sites, *banned_args = sys.argv[1:]
banned = {Path(entry).resolve() for entry in banned_args}
for directory in sites.split("|"):
    if directory:
        site.addsitedir(directory)
sys.path[:] = [
    entry
    for entry in sys.path
    if not entry or Path(entry).resolve() not in banned
]
try:
    import installer
    import installer.matrix
except Exception as exc:
    sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
    raise SystemExit(1)
installed = Path(installer.__file__).resolve().parent / "providers.json"
matrix_path = Path(installer.matrix.MATRIX_PATH).resolve()
if matrix_path != installed:
    sys.stderr.write(f"{matrix_path} is not the installed providers.json\n")
    raise SystemExit(1)
try:
    rows = installer.matrix.load_matrix()
except Exception as exc:
    sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
    raise SystemExit(1)
if not rows:
    sys.stderr.write("provider matrix is empty\n")
    raise SystemExit(1)
"""


def _ignore_copy(directory: str, names: list[str]) -> set[str]:
    skipped = {"__pycache__", "node_modules", ".venv", "dist", "build"}
    return {
        name
        for name in names
        if name in skipped or name.endswith(".pyc") or name.endswith(".egg-info")
    }


def _copy_source(destination: Path) -> Path:
    destination.mkdir(parents=True)
    for name in ("pyproject.toml", "README.md"):
        shutil.copy2(REPO_ROOT / name, destination / name)
    for name in ("orchestra", "dashboard", "installer", "scripts"):
        shutil.copytree(
            REPO_ROOT / name,
            destination / name,
            symlinks=True,
            ignore=_ignore_copy,
        )
    return destination


def _site_dirs(prefix: Path) -> list[Path]:
    purelib = Path(
        sysconfig.get_path("purelib", vars={"base": str(prefix), "platbase": str(prefix)})
    )
    found = [purelib, *prefix.glob("**/site-packages"), *prefix.glob("**/dist-packages")]
    return sorted({path for path in found if path.is_dir()})


def _pip_install(prefix: Path, source: Path, *, editable: bool) -> None:
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--prefix",
        str(prefix),
        "--no-build-isolation",
        "--no-warn-script-location",
        "--disable-pip-version-check",
    ]
    if editable:
        command.append("-e")
    command.append(str(source))
    proc = subprocess.run(command, capture_output=True, text=True)
    assert proc.returncode == 0, (proc.stderr or proc.stdout).strip().splitlines()[-1]


class _Install:
    def __init__(self, prefix: Path, source: Path) -> None:
        self.prefix = prefix
        self.source = source

    def sites(self) -> str:
        return "|".join(str(path) for path in _site_dirs(self.prefix))


def _make_install(base: Path, *, editable: bool) -> _Install:
    source = _copy_source(base / "source")
    prefix = base / "prefix"
    _pip_install(prefix, source, editable=editable)
    return _Install(prefix, source)


@pytest.fixture(scope="module")
def editable_install(tmp_path_factory: pytest.TempPathFactory) -> _Install:
    return _make_install(tmp_path_factory.mktemp("editable-install"), editable=True)


@pytest.fixture(scope="module")
def wheel_install(tmp_path_factory: pytest.TempPathFactory) -> _Install:
    return _make_install(tmp_path_factory.mktemp("wheel-install"), editable=False)


def _assert_success(proc: subprocess.CompletedProcess[str]) -> None:
    lines = (proc.stderr or proc.stdout or "").strip().splitlines()
    assert proc.returncode == 0, lines[-1] if lines else f"exit {proc.returncode}"


def _run_install_import(installed: _Install, module: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            _IMPORT_IN_INSTALL,
            installed.sites(),
            module,
            str(installed.source.resolve()),
            str(REPO_ROOT.resolve()),
        ],
        capture_output=True,
        text=True,
    )


def test_r1_dashboard(editable_install: _Install) -> None:
    """R1: An editable install imports `dashboard` when the repository root is absent from `sys.path`."""
    _assert_success(_run_install_import(editable_install, "dashboard"))


def test_r2_dashboard_backend_server(editable_install: _Install) -> None:
    """R2: An editable install imports `dashboard.backend.server` when the repository root is absent from `sys.path`."""
    _assert_success(_run_install_import(editable_install, "dashboard.backend.server"))


def test_r3_installer(editable_install: _Install) -> None:
    """R3: An editable install imports `installer` when the repository root is absent from `sys.path`."""
    _assert_success(_run_install_import(editable_install, "installer"))


def test_r4_installer_adapters(editable_install: _Install) -> None:
    """R4: An editable install imports `installer.adapters` when the repository root is absent from `sys.path`."""
    _assert_success(_run_install_import(editable_install, "installer.adapters"))


def test_r7_fastapi(editable_install: _Install) -> None:
    """R7: That install imports `fastapi`."""
    _assert_success(_run_install_import(editable_install, "fastapi"))


def test_r8_uvicorn(editable_install: _Install) -> None:
    """R8: That install imports `uvicorn`."""
    _assert_success(_run_install_import(editable_install, "uvicorn"))


def test_r27_providers_json(wheel_install: _Install) -> None:
    """R27: `installer.matrix` loads `providers.json` from the installed `installer` package."""
    proc = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            _PROVIDERS_JSON,
            wheel_install.sites(),
            str(wheel_install.source.resolve()),
            str(REPO_ROOT.resolve()),
        ],
        capture_output=True,
        text=True,
    )
    _assert_success(proc)


def test_r9_canon_import() -> None:
    """R9: Importing `orchestra.cli` raises `ModuleNotFoundError` when `orchestra.canon` cannot be imported."""
    proc = subprocess.run(
        [sys.executable, "-I", "-c", _BLOCKED_CLI_IMPORT, str(REPO_ROOT), "orchestra.canon"],
        capture_output=True,
        text=True,
    )
    _assert_success(proc)


def test_r10_suite_import() -> None:
    """R10: Importing `orchestra.cli` raises `ModuleNotFoundError` when `orchestra.conductor.suite` cannot be imported."""
    proc = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            _BLOCKED_CLI_IMPORT,
            str(REPO_ROOT),
            "orchestra.conductor.suite",
        ],
        capture_output=True,
        text=True,
    )
    _assert_success(proc)


def test_r11_check_import() -> None:
    """R11: Importing `orchestra.cli` raises `ModuleNotFoundError` when `orchestra.conductor.check` cannot be imported."""
    proc = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            _BLOCKED_CLI_IMPORT,
            str(REPO_ROOT),
            "orchestra.conductor.check",
        ],
        capture_output=True,
        text=True,
    )
    _assert_success(proc)


def test_r15_effort_rollup() -> None:
    """R15: Importing `effort_rollup` from `orchestra.score` succeeds without inserting `scripts/` on `sys.path`."""
    proc = subprocess.run(
        [sys.executable, "-I", "-c", _EFFORT_ROLLUP, str(REPO_ROOT)],
        capture_output=True,
        text=True,
    )
    _assert_success(proc)


def test_r12_report_no_sys_path() -> None:
    """R12: `orchestra.sessions.report` does not insert a directory on `sys.path`."""
    proc = subprocess.run(
        [sys.executable, "-I", "-c", _NO_SYSPATH_INSERT, str(REPO_ROOT), "report"],
        capture_output=True,
        text=True,
    )
    _assert_success(proc)


def test_r13_aggregate_no_sys_path() -> None:
    """R13: `orchestra.sessions.aggregate` does not insert a directory on `sys.path`."""
    proc = subprocess.run(
        [sys.executable, "-I", "-c", _NO_SYSPATH_INSERT, str(REPO_ROOT), "aggregate"],
        capture_output=True,
        text=True,
    )
    _assert_success(proc)


def test_r14_scripts_not_symlink() -> None:
    """R14: `orchestra/_scripts` is not a symlink."""
    path = REPO_ROOT / "orchestra" / "_scripts"
    assert not path.is_symlink(), f"{path} is a symlink"
