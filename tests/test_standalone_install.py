"""Packaged payload and tool-install planning for ``orchestra install``."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MARKER = ".orchestra-install.json"
DIRECT_URL = "file:///opt/orchestra-standalone-direct"
MANUAL_COMMAND = "uv tool install git+https://github.com/andrewy1n/orchestra"
PAYLOAD_ROOTS = ("skills", "agents", "hosts")

UV_STUB = """#!/bin/sh
printf '%s\\n' "$*" >> "$ORCHESTRA_UV_LOG"
exit 0
"""

HOOKS_PAYLOAD = {
    "hooks": {
        "SessionStart": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "orchestra hook-start",
                        "timeout": 30,
                    }
                ]
            }
        ]
    }
}


def _payload_files() -> tuple[str, ...]:
    relatives: list[str] = []
    for root_name in PAYLOAD_ROOTS:
        root = REPO_ROOT / root_name
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            if path.suffix in {".pyc", ".pyo"} or path.name == "__pycache__":
                continue
            relatives.append(path.relative_to(REPO_ROOT).as_posix())
    return tuple(relatives)


def _ignore_copy(directory: str, names: list[str]) -> set[str]:
    skipped = {"__pycache__", ".venv", "dist", "build", "node_modules", ".canon", ".git"}
    return {
        name
        for name in names
        if name in skipped or name.endswith(".pyc") or name.endswith(".egg-info")
    }


def _isolated_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("VIRTUAL_ENV", None)
    return env


def _build_wheel(work: Path) -> Path:
    source = work / "source"
    source.mkdir(parents=True)
    for name in ("pyproject.toml", "README.md", "MANIFEST.in"):
        original = REPO_ROOT / name
        if original.is_file():
            shutil.copy2(original, source / name)
    for name in ("orchestra", "dashboard", "installer", *PAYLOAD_ROOTS):
        shutil.copytree(REPO_ROOT / name, source / name, symlinks=True, ignore=_ignore_copy)
    wheel_dir = work / "wheels"
    wheel_dir.mkdir()
    built = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-build-isolation",
            "--disable-pip-version-check",
            "--wheel-dir",
            str(wheel_dir),
            str(source),
        ],
        cwd=work,
        env=_isolated_env(),
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert built.returncode == 0, (built.stderr or built.stdout)[-2000:]
    wheels = sorted(wheel_dir.glob("*.whl"))
    assert len(wheels) == 1, [path.name for path in wheels]
    return wheels[0]


def _wheel_names(wheel: Path) -> set[str]:
    with zipfile.ZipFile(wheel) as archive:
        return set(archive.namelist())


def _wheel_has(names: set[str], relative: str) -> bool:
    suffix = "/" + relative
    for name in names:
        if name != relative and not name.endswith(suffix):
            continue
        parts = Path(name).parts
        if ".canon" in parts or "dashboard" in parts:
            continue
        return True
    return False


def _fingerprint(root: Path) -> tuple[tuple[str, bytes], ...]:
    rows: list[tuple[str, bytes]] = []
    if not root.exists():
        return ()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            rows.append((relative, b"link:" + os.readlink(path).encode()))
        elif path.is_file():
            rows.append((relative, path.read_bytes()))
    return tuple(rows)


def _payload_fingerprint() -> tuple[tuple[str, bytes], ...]:
    rows: list[tuple[str, bytes]] = []
    for name in PAYLOAD_ROOTS:
        for relative, data in _fingerprint(REPO_ROOT / name):
            rows.append((f"{name}/{relative}", data))
    return tuple(rows)


def _write_executable(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _tool_path(bin_dir: Path, *, orchestra: bool, uv_log: Path | None) -> str:
    bin_dir.mkdir(parents=True, exist_ok=True)
    if orchestra:
        _write_executable(bin_dir / "orchestra", "#!/bin/sh\nexit 0\n")
    if uv_log is not None:
        _write_executable(bin_dir / "uv", UV_STUB)
    return os.pathsep.join((str(bin_dir), "/usr/bin", "/bin"))


def _direct_url_site(root: Path, url: str | None) -> Path:
    site = root / "site"
    dist = site / "orchestra-0.1.0.dist-info"
    dist.mkdir(parents=True)
    (dist / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: orchestra\nVersion: 0.1.0\n",
        encoding="utf-8",
    )
    if url is not None:
        (dist / "direct_url.json").write_text(
            json.dumps({"url": url, "dir_info": {"editable": False}}) + "\n",
            encoding="utf-8",
        )
    return site


def _uv_calls(log: Path) -> list[str]:
    if not log.is_file():
        return []
    return [line for line in log.read_text(encoding="utf-8").splitlines() if line]


def _marker(home: Path) -> dict[str, object] | None:
    path = home / ".claude" / MARKER
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    return payload


@pytest.fixture(scope="module")
def built_wheel(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _build_wheel(tmp_path_factory.mktemp("standalone-wheel"))


@pytest.fixture(scope="module")
def wheel_venv(built_wheel: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    base = tmp_path_factory.mktemp("standalone-venv")
    venv = base / "venv"
    isolated = _isolated_env()
    created = subprocess.run(
        [sys.executable, "-m", "venv", str(venv)],
        env=isolated,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert created.returncode == 0, created.stderr
    installed = subprocess.run(
        [
            str(venv / "bin" / "pip"),
            "install",
            "--disable-pip-version-check",
            str(built_wheel),
        ],
        env=isolated,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert installed.returncode == 0, (installed.stderr or installed.stdout)[-2000:]
    assert (venv / "bin" / "orchestra").is_file()
    return venv


@pytest.fixture()
def source(tmp_path: Path) -> Path:
    root = tmp_path / "checkout"
    skill = root / "skills" / "init"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: init\ndescription: fixture\n---\n",
        encoding="utf-8",
    )
    hooks = root / "hosts" / "claude" / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "hooks.json").write_text(json.dumps(HOOKS_PAYLOAD) + "\n", encoding="utf-8")
    (root / ".git").write_text("gitdir: fixture\n", encoding="utf-8")
    return root


def _run_checkout(
    *args: str,
    project: Path,
    source: Path,
    home: Path,
    path: str,
    site: Path | None = None,
    uv_log: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    entries = [str(REPO_ROOT)]
    if site is not None:
        entries.insert(0, str(site))
    env["PYTHONPATH"] = os.pathsep.join(entries)
    env["ORCHESTRA_INSTALL_SOURCE"] = str(source)
    env["PATH"] = path
    env["HOME"] = str(home)
    if uv_log is not None:
        env["ORCHESTRA_UV_LOG"] = str(uv_log)
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "install", *args],
        cwd=str(project),
        env=env,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        timeout=60,
    )


def _run_packaged(venv: Path, home: Path, project: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("ORCHESTRA_INSTALL_SOURCE", None)
    env["VIRTUAL_ENV"] = str(venv)
    env["PATH"] = os.pathsep.join((str(venv / "bin"), "/usr/bin", "/bin"))
    env["HOME"] = str(home)
    return subprocess.run(
        [
            str(venv / "bin" / "orchestra"),
            "install",
            "--yes",
            "--only",
            "claude",
            "--home",
            str(home),
        ],
        cwd=str(project),
        env=env,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        timeout=60,
    )


def test_wheel_contains_payload(built_wheel: Path) -> None:
    """R1: The built wheel contains the skills, agents, and hosts payload files."""
    names = _wheel_names(built_wheel)
    assert all(".canon" not in Path(name).parts for name in names)
    relatives = _payload_files()
    assert any(relative.startswith("skills/") for relative in relatives)
    assert any(relative.startswith("agents/") for relative in relatives)
    assert any(relative.startswith("hosts/") for relative in relatives)
    missing = [relative for relative in relatives if not _wheel_has(names, relative)]
    assert not missing


def test_packaged_payload(wheel_venv: Path, tmp_path: Path) -> None:
    """R2: With no checkout, `orchestra install` reads the packaged payload."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    before = _payload_fingerprint()
    proc = _run_packaged(wheel_venv, home, project)
    assert _payload_fingerprint() == before
    marker = _marker(home)
    source_text = marker.get("source") if marker else None
    source = Path(source_text).resolve() if isinstance(source_text, str) else None
    installed = home / ".claude" / "skills" / "init" / "SKILL.md"
    packaged = source / "skills" / "init" / "SKILL.md" if source is not None else None
    output = proc.stdout + proc.stderr
    assert source is not None, output
    assert source != REPO_ROOT.resolve()
    assert REPO_ROOT.resolve() not in source.parents
    assert ".canon" not in source.parts
    assert "dashboard" not in source.parts
    assert packaged is not None and packaged.is_file(), output
    assert installed.is_file(), output
    assert installed.read_text(encoding="utf-8") == packaged.read_text(encoding="utf-8")


def test_packaged_defaults_to_copy(wheel_venv: Path, tmp_path: Path) -> None:
    """R3: With the packaged payload as source, the install mode defaults to copy."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    before = _payload_fingerprint()
    proc = _run_packaged(wheel_venv, home, project)
    assert _payload_fingerprint() == before
    marker = _marker(home)
    mode = marker.get("mode") if marker else None
    skill = home / ".claude" / "skills" / "init"
    output = proc.stdout + proc.stderr
    assert mode == "copy", output
    assert skill.is_dir(), output
    assert not skill.is_symlink()
    assert (skill / "SKILL.md").is_file()
    assert not (skill / "SKILL.md").is_symlink()


def test_checkout_defaults_to_symlink(tmp_path: Path) -> None:
    """R4: With a checkout as source, the install mode defaults to symlink."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    before = _payload_fingerprint()
    proc = _run_checkout(
        "--yes",
        "--only",
        "claude",
        "--home",
        str(home),
        project=project,
        source=REPO_ROOT,
        home=home,
        path=os.pathsep.join(("/usr/bin", "/bin")),
    )
    assert _payload_fingerprint() == before
    assert proc.returncode == 0, proc.stdout + proc.stderr
    skill = home / ".claude" / "skills" / "init"
    assert skill.is_symlink()
    assert skill.resolve() == (REPO_ROOT / "skills" / "init").resolve()
    marker = _marker(home)
    assert marker is not None
    assert marker.get("mode") == "symlink"


def test_wheel_installs_claude_payload(wheel_venv: Path, tmp_path: Path) -> None:
    """R5: A wheel installed into a clean virtualenv installs the Claude payload into a temporary home."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    before = _payload_fingerprint()
    proc = _run_packaged(wheel_venv, home, project)
    assert _payload_fingerprint() == before
    output = proc.stdout + proc.stderr
    init_skill = home / ".claude" / "skills" / "init" / "SKILL.md"
    assert init_skill.is_file(), output
    assert REPO_ROOT.resolve() not in init_skill.resolve().parents
    expected = (REPO_ROOT / "skills" / "init" / "SKILL.md").read_text(encoding="utf-8")
    assert init_skill.read_text(encoding="utf-8") == expected
    engage = home / ".claude" / "skills" / "engage" / "SKILL.md"
    assert engage.is_file(), output
    assert engage.read_text(encoding="utf-8") == (
        REPO_ROOT / "skills" / "engage" / "SKILL.md"
    ).read_text(encoding="utf-8")
    hooks = home / ".claude" / "hooks" / "hooks.json"
    assert hooks.is_file(), output
    assert hooks.read_text(encoding="utf-8") == (
        REPO_ROOT / "hosts" / "claude" / "hooks" / "hooks.json"
    ).read_text(encoding="utf-8")
    assert (home / ".claude" / "agents" / "reviewer.md").is_file(), output
    assert (home / ".claude" / "settings.json").is_file(), output
    assert not any(
        part in {".canon", "dashboard"} for path in home.rglob("*") for part in path.parts
    )


def test_tool_step_when_missing(tmp_path: Path, source: Path) -> None:
    """R6: The plan lists a tool-install step when `orchestra` is not on PATH."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    site = _direct_url_site(tmp_path / "meta", DIRECT_URL)
    proc = _run_checkout(
        "--dry-run",
        "--only",
        "claude",
        "--home",
        str(home),
        project=project,
        source=source,
        home=home,
        path=_tool_path(tmp_path / "bin", orchestra=False, uv_log=None),
        site=site,
    )
    output = proc.stdout + proc.stderr
    assert "tool-install" in output, output


def test_no_tool_step_when_present(tmp_path: Path, source: Path) -> None:
    """R7: The plan lists no tool-install step when `orchestra` is on PATH."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    site = _direct_url_site(tmp_path / "meta", DIRECT_URL)
    proc = _run_checkout(
        "--dry-run",
        "--only",
        "claude",
        "--home",
        str(home),
        project=project,
        source=source,
        home=home,
        path=_tool_path(tmp_path / "bin", orchestra=True, uv_log=None),
        site=site,
    )
    output = proc.stdout + proc.stderr
    assert proc.returncode == 0, output
    assert "tool-install" not in output
    assert "uv tool install" not in output
    assert DIRECT_URL not in output


def test_tool_step_direct_url(tmp_path: Path, source: Path) -> None:
    """R8: The tool-install step installs from the direct URL of the running package."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    site = _direct_url_site(tmp_path / "meta", DIRECT_URL)
    proc = _run_checkout(
        "--dry-run",
        "--only",
        "claude",
        "--home",
        str(home),
        project=project,
        source=source,
        home=home,
        path=_tool_path(tmp_path / "bin", orchestra=False, uv_log=None),
        site=site,
    )
    output = proc.stdout + proc.stderr
    assert f"uv tool install {DIRECT_URL}" in output, output


def test_tool_step_manual_command(tmp_path: Path, source: Path) -> None:
    """R9: When the package has no direct-URL record, the plan prints the manual `uv tool install` command and runs nothing."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    site = _direct_url_site(tmp_path / "meta", None)
    log = tmp_path / "uv.log"
    before = _fingerprint(source)
    proc = _run_checkout(
        "--only",
        "claude",
        "--home",
        str(home),
        project=project,
        source=source,
        home=home,
        path=_tool_path(tmp_path / "bin", orchestra=False, uv_log=log),
        site=site,
        uv_log=log,
    )
    output = proc.stdout + proc.stderr
    assert MANUAL_COMMAND in output, output
    assert _uv_calls(log) == []
    assert _fingerprint(source) == before


def test_tool_step_dry_run(tmp_path: Path, source: Path) -> None:
    """R10: A dry run prints the tool-install step and runs nothing."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    site = _direct_url_site(tmp_path / "meta", DIRECT_URL)
    log = tmp_path / "uv.log"
    before = _fingerprint(source)
    proc = _run_checkout(
        "--dry-run",
        "--only",
        "claude",
        "--home",
        str(home),
        project=project,
        source=source,
        home=home,
        path=_tool_path(tmp_path / "bin", orchestra=False, uv_log=log),
        site=site,
        uv_log=log,
    )
    output = proc.stdout + proc.stderr
    assert "tool-install" in output, output
    assert DIRECT_URL in output, output
    assert _uv_calls(log) == []
    assert not (home / ".claude").exists()
    assert _fingerprint(source) == before


def test_tool_step_yes(tmp_path: Path, source: Path) -> None:
    """R11: With --yes, the tool-install step runs without a prompt."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    site = _direct_url_site(tmp_path / "meta", DIRECT_URL)
    log = tmp_path / "uv.log"
    before = _fingerprint(source)
    proc = _run_checkout(
        "--yes",
        "--only",
        "claude",
        "--home",
        str(home),
        project=project,
        source=source,
        home=home,
        path=_tool_path(tmp_path / "bin", orchestra=False, uv_log=log),
        site=site,
        uv_log=log,
    )
    output = proc.stdout + proc.stderr
    calls = _uv_calls(log)
    assert any("install" in line and DIRECT_URL in line for line in calls), output
    assert "[Y/n]" not in output
    assert "[y/N]" not in output
    assert "Proceed?" not in output
    assert _fingerprint(source) == before
