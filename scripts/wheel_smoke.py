#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIST = ROOT / "dashboard" / "frontend" / "dist"
_READY_TIMEOUT = 60.0
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
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    args = parser.parse_args(argv)
    if args.wheel is None and not (args.dist / "index.html").is_file():
        sys.stderr.write(
            f"{args.dist / 'index.html'} is missing; "
            "run `npm run build` in dashboard/frontend first or pass --dist\n"
        )
        return 1
    base = _base_env()
    with tempfile.TemporaryDirectory(prefix="wheel-smoke-") as tmp_name:
        tmp = Path(tmp_name)
        if args.wheel is None:
            wheel = _build_wheel(tmp / "source", base, args.dist)
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


def _build_wheel(source: Path, env: dict[str, str], dist: Path) -> Path:
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
    shutil.copytree(dist, source / "dashboard" / "frontend" / "dist", dirs_exist_ok=True)
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
        ("import dashboard.backend.server", [str(python), "-c", "import dashboard.backend.server"], work, None),
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
    served = _root_check(work, repo, python, env)
    print(f"GET /: {'pass' if served else 'fail'}")
    return 1 if failed or not served else 0


def _root_check(work: Path, repo: Path, python: Path, env: dict[str, str]) -> bool:
    located = _run(
        [str(python), "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
        cwd=work,
        env=env,
    )
    if located.returncode != 0:
        return False
    index = Path(located.stdout.strip()) / "dashboard" / "frontend" / "dist" / "index.html"
    if not index.is_file():
        sys.stderr.write(f"{index} is not in the installed wheel\n")
        return False
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    log = work / "server.log"
    with log.open("wb") as sink:
        server = subprocess.Popen(
            [str(python), "-m", "dashboard.backend.server", "--port", str(port)],
            cwd=repo,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=sink,
            stderr=subprocess.STDOUT,
        )
        try:
            return _serves_index(server, port, index)
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()


def _serves_index(server: subprocess.Popen[bytes], port: int, index: Path) -> bool:
    url = f"http://127.0.0.1:{port}/"
    deadline = time.monotonic() + _READY_TIMEOUT
    while time.monotonic() < deadline:
        if server.poll() is not None:
            sys.stderr.write(f"server exited with {server.returncode}\n")
            return False
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                return response.status == 200 and response.read() == index.read_bytes()
        except urllib.error.HTTPError as exc:
            sys.stderr.write(f"GET / returned {exc.code}\n")
            return False
        except (urllib.error.URLError, OSError):
            time.sleep(0.2)
    sys.stderr.write("server did not answer in time\n")
    return False


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
