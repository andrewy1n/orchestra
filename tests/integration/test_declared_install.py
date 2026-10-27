"""Clean ``orchestra install`` into a temporary environment (R5, R6)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]

def _run(
    cmd: list[str],
    *,
    env: dict[str, str],
    cwd: Path,
    timeout: float = 180,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode()
        if isinstance(stderr, bytes):
            stderr = stderr.decode()
        return subprocess.CompletedProcess(cmd, 124, stdout, stderr + "\ntimeout")


def _source_tree(dest: Path) -> Path:
    """Copy the install inputs so the build does not write into the checkout."""
    source = dest / "source"
    source.mkdir()
    for name in ("pyproject.toml", "README.md"):
        shutil.copy2(_ROOT / name, source / name)
    for name in ("orchestra", "scripts"):
        shutil.copytree(
            _ROOT / name,
            source / name,
            symlinks=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"),
        )
    return source


def _clean_environment(tmp_path: Path) -> tuple[Path, dict[str, str], Path]:
    """A temporary venv that provides ``orchestra`` and none of its dependencies."""
    venv = tmp_path / "env"
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()
    created = _run([sys.executable, "-m", "venv", str(venv)], env=os.environ.copy(), cwd=tmp_path)
    assert created.returncode == 0, created.stderr
    source = _source_tree(tmp_path)
    installed = _run(
        [str(venv / "bin" / "python"), "-m", "pip", "install", "--no-deps", str(source)],
        env=os.environ.copy(),
        cwd=tmp_path,
    )
    assert installed.returncode == 0, installed.stdout + installed.stderr
    env = {
        "PATH": os.pathsep.join([str(venv / "bin"), os.environ.get("PATH", "")]),
        "HOME": str(home),
        "VIRTUAL_ENV": str(venv),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
    }
    for key in ("LANG", "LC_ALL", "TMPDIR"):
        if key in os.environ:
            env[key] = os.environ[key]
    return venv, env, project


def test_r5_clean_install_imports_components(tmp_path: Path):
    """R5: a clean install can import canon and tuner and run both CLIs."""
    venv, env, project = _clean_environment(tmp_path)
    orchestra = str(venv / "bin" / "orchestra")
    installed = _run([orchestra, "install"], env=env, cwd=project)
    imported = _run(
        [str(venv / "bin" / "python"), "-c", "import orchestra.canon, orchestra.tuner"],
        env=env,
        cwd=project,
    )
    helped = _run([orchestra, "--help"], env=env, cwd=project)
    canon_help = _run([str(venv / "bin" / "canon"), "--help"], env=env, cwd=project)
    assert imported.returncode == 0 and helped.returncode == 0 and canon_help.returncode == 0, (
        "clean orchestra install did not leave canon and tuner importable "
        f"and both CLIs exiting 0; "
        f"import={imported.returncode} help={helped.returncode} "
        f"install={installed.returncode}\n"
        f"{imported.stderr}\n{helped.stderr}\n{installed.stderr}"
    )
