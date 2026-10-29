#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_WHEEL_NAME = re.compile(
    r"^[A-Za-z0-9_.]+-[A-Za-z0-9_.!+]+-"
    r"[A-Za-z0-9_.]+-[A-Za-z0-9_.]+-[A-Za-z0-9_.]+\.whl$"
)

_DROPPED_ENV = (
    "VIRTUAL_ENV",
    "UV_PROJECT",
    "UV_PROJECT_ENVIRONMENT",
    "CANON_SCHEMA_PATH",
    "CANON_READONLY",
    "PYTHONHOME",
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel", type=Path)
    args = parser.parse_args(argv)
    base = _base_env()
    with tempfile.TemporaryDirectory(prefix="wheel-smoke-") as tmp_name:
        tmp = Path(tmp_name)
        if args.wheel is None:
            wheel = _build_wheel(tmp / "source", base)
        else:
            wheel = args.wheel
        venv = tmp / "venv"
        created = _run(["uv", "venv", str(venv)], cwd=tmp, env=base)
        if created.returncode != 0:
            return 1
        python = _venv_python(venv)
        env = dict(base)
        env["VIRTUAL_ENV"] = str(venv)
        env["PATH"] = str(python.parent) + os.pathsep + env.get("PATH", "")
        installed = _run(
            ["uv", "pip", "install", "--python", str(python), os.fspath(_installable(wheel))],
            cwd=tmp,
            env=env,
        )
        if installed.returncode != 0:
            return 1
        return _checks(tmp, venv, python, env)


def _base_env() -> dict[str, str]:
    env = os.environ.copy()
    root = ROOT.resolve()
    kept: list[str] = []
    for entry in env.get("PYTHONPATH", "").split(os.pathsep):
        if not entry:
            continue
        try:
            path = Path(entry).resolve()
        except OSError:
            kept.append(entry)
            continue
        if path == root or root in path.parents:
            continue
        kept.append(entry)
    if kept:
        env["PYTHONPATH"] = os.pathsep.join(kept)
    else:
        env.pop("PYTHONPATH", None)
    for name in _DROPPED_ENV:
        env.pop(name, None)
    return env


def _outside_checkout(path: Path) -> None:
    resolved = path.resolve()
    root = ROOT.resolve()
    if resolved == root or root in resolved.parents:
        sys.stderr.write(f"{path} is inside the checkout\n")
        raise SystemExit(1)


def _build_wheel(source: Path, env: dict[str, str]) -> Path:
    source.mkdir()
    _outside_checkout(source)
    archived = subprocess.run(
        ["git", "-C", str(ROOT), "archive", "HEAD"],
        cwd=source,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if archived.returncode != 0:
        sys.stderr.write(archived.stderr.decode(errors="replace"))
        raise SystemExit(1)
    extracted = subprocess.run(
        ["tar", "-x", "-C", str(source)],
        input=archived.stdout,
        cwd=source,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if extracted.returncode != 0:
        sys.stderr.write(extracted.stderr.decode(errors="replace"))
        raise SystemExit(1)
    built = subprocess.run(
        ["uv", "build", "--wheel"],
        cwd=source,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if built.returncode != 0:
        sys.stderr.write(built.stderr.decode(errors="replace"))
        sys.stderr.write(built.stdout.decode(errors="replace"))
        raise SystemExit(1)
    wheels = sorted((source / "dist").glob("*.whl"))
    if len(wheels) != 1:
        sys.stderr.write(f"expected one wheel, found {[path.name for path in wheels]}\n")
        raise SystemExit(1)
    return wheels[0]


def _installable(wheel: Path) -> Path:
    if _WHEEL_NAME.fullmatch(wheel.name):
        return wheel
    alias = Path(tempfile.mkdtemp(prefix="wheel-smoke-alias-")) / _canonical_wheel_name(wheel)
    alias.symlink_to(wheel.resolve())
    return alias


def _canonical_wheel_name(wheel: Path) -> str:
    with zipfile.ZipFile(wheel) as archive:
        info_name = next(
            name
            for name in archive.namelist()
            if name.endswith(".dist-info/WHEEL") and name.count("/") == 1
        )
        dist = info_name.split("/", 1)[0][: -len(".dist-info")]
        tag = "py3-none-any"
        for line in archive.read(info_name).decode().splitlines():
            if line.startswith("Tag:"):
                tag = line.split(":", 1)[1].strip()
                break
    return f"{dist}-{tag}.whl"


def _venv_python(venv: Path) -> Path:
    for candidate in (venv / "bin" / "python", venv / "Scripts" / "python.exe"):
        if candidate.is_file():
            return candidate
    sys.stderr.write(f"uv venv did not create a python in {venv}\n")
    raise SystemExit(1)


def _checks(tmp: Path, venv: Path, python: Path, env: dict[str, str]) -> int:
    work = tmp / "work"
    repo = tmp / "repo"
    work.mkdir()
    repo.mkdir()
    _outside_checkout(work)
    _outside_checkout(repo)
    git_init = _run(["git", "init"], cwd=repo, env=env)
    if git_init.returncode != 0:
        return 1
    bindir = python.parent
    orchestra = bindir / "orchestra"
    canon = bindir / "canon"
    checks: list[tuple[str, list[str], Path, str | None]] = [
        ("orchestra --help", [str(orchestra), "--help"], work, None),
        ("canon --help", [str(canon), "--help"], work, None),
        (
            "canon init",
            [str(canon), "init", "--schemas", "score,conductor,tuner"],
            repo,
            None,
        ),
        ("canon validate", [str(canon), "validate"], repo, None),
        ("orchestra install --list", [str(orchestra), "install", "--list"], work, "claude"),
        ("import dashboard", [str(python), "-c", "import dashboard"], work, None),
        ("import dashboard.web", [str(python), "-c", "import dashboard.web"], work, None),
        ("import installer", [str(python), "-c", "import installer"], work, None),
        (
            "import installer.adapters",
            [str(python), "-c", "import installer.adapters"],
            work,
            None,
        ),
    ]
    failed = False
    for name, command, cwd, needle in checks:
        try:
            result = _run(command, cwd=cwd, env=env)
        except OSError as exc:
            print(f"{name}: fail")
            sys.stderr.write(f"{exc}\n")
            failed = True
            continue
        ok = result.returncode == 0
        if ok and needle is not None and re.search(rf"\b{needle}\b", result.stdout or "") is None:
            ok = False
            sys.stderr.write(result.stdout or "")
            sys.stderr.write(f"{name}: output did not name {needle}\n")
        print(f"{name}: {'pass' if ok else 'fail'}")
        failed = failed or not ok
    return 1 if failed else 0


def _run(
    command: list[str], *, cwd: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr or "")
        if result.stdout:
            sys.stderr.write(result.stdout)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
