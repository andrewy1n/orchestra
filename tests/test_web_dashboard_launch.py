"""Launcher oracles for the web dashboard.

The web launcher is dashboard/bin/web. It follows the same store resolution as
dashboard/bin/dashboard (dashboard.artifact_store.resolve) and serves the Vite
production build from `npm run build` in dashboard/web/ui, at
dashboard/web/ui/dist/index.html.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


import helpers as h
from conftest import REPO_ROOT, run_cli

sys.path.insert(0, str(REPO_ROOT))
from orchestra.canon.project import open_store  # noqa: E402
from dashboard import model  # noqa: E402

SCRIPT = REPO_ROOT / "dashboard" / "bin" / "web"
DIST_INDEX = REPO_ROOT / "dashboard" / "web" / "ui" / "dist" / "index.html"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _env(home: Path | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    if home is not None:
        env["HOME"] = str(home)
    return env


def _spawn(cwd: Path, args: list[str], env: dict[str, str], out: Path, err: Path) -> subprocess.Popen:
    assert SCRIPT.is_file(), f"web launcher missing: {SCRIPT}"
    stdout = out.open("w")
    stderr = err.open("w")
    try:
        return subprocess.Popen(
            [str(SCRIPT), *args], cwd=str(cwd), env=env,
            stdout=stdout, stderr=stderr, text=True, start_new_session=True,
        )
    except FileNotFoundError:
        proc = None
    assert proc is not None, f"web launcher missing: {SCRIPT}"
    return proc


def _stop(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=3)


def _ppid(pid: int) -> int | None:
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return None
    fields = stat[stat.rfind(")") + 2:].split()
    return int(fields[1]) if len(fields) > 1 else None


def _descendants(pid: int) -> set[int]:
    parents: dict[int, int] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        child = int(entry.name)
        parent = _ppid(child)
        if parent is not None:
            parents[child] = parent
    found = {pid}
    changed = True
    while changed:
        changed = False
        for child, parent in parents.items():
            if parent in found and child not in found:
                found.add(child)
                changed = True
    return found


def _listen_addresses(pid: int) -> list[str]:
    inodes: set[str] = set()
    for owner in _descendants(pid):
        fd_dir = Path(f"/proc/{owner}/fd")
        if not fd_dir.is_dir():
            continue
        for fd in fd_dir.iterdir():
            try:
                target = os.readlink(fd)
            except OSError:
                continue
            if target.startswith("socket:[") and target.endswith("]"):
                inodes.add(target[len("socket:["):-1])
    addresses = []
    for name, family in (("/proc/net/tcp", socket.AF_INET), ("/proc/net/tcp6", socket.AF_INET6)):
        try:
            lines = Path(name).read_text().splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            parts = line.split()
            if len(parts) < 10 or parts[3] != "0A" or parts[9] not in inodes:
                continue
            host_hex, _port_hex = parts[1].split(":")
            raw = bytes.fromhex(host_hex)
            if family is socket.AF_INET:
                addresses.append(socket.inet_ntoa(raw[::-1]))
            else:
                words = [raw[index:index + 4][::-1] for index in range(0, 16, 4)]
                addresses.append(socket.inet_ntop(socket.AF_INET6, b"".join(words)))
    return addresses


def _await_listen(proc: subprocess.Popen, err: Path, timeout: float = 20) -> list[str]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            break
        addresses = _listen_addresses(proc.pid)
        if addresses:
            return addresses
        time.sleep(0.05)
    detail = err.read_text() if err.is_file() else ""
    assert False, f"web launcher did not listen (exit {proc.poll()}): {detail}"


def _get(port: int, path: str) -> tuple[int, str, bytes]:
    url = f"http://127.0.0.1:{port}{path}"
    deadline = time.time() + 30
    last: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.status, response.headers.get("Content-Type", ""), response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers.get("Content-Type", ""), exc.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last = exc
            time.sleep(0.1)
    assert False, f"GET {path} on 127.0.0.1:{port} failed: {last}"


def test_r1_loopback(store, tmp_path, monkeypatch):
    assert SCRIPT.is_file(), f"web launcher missing: {SCRIPT}"
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    port = _free_port()
    proc = _spawn(store, ["--port", str(port)], _env(tmp_path / "home"), tmp_path / "out", tmp_path / "err")
    try:
        addresses = _await_listen(proc, tmp_path / "err")
        assert addresses == ["127.0.0.1"] or set(addresses) == {"127.0.0.1"}
        with socket.create_connection(("127.0.0.1", port), timeout=5):
            pass
    finally:
        _stop(proc)

    other = _free_port()
    proc = _spawn(
        store, ["--port", str(other), "--host", "0.0.0.0"],
        _env(tmp_path / "home"), tmp_path / "out-wide", tmp_path / "err-wide",
    )
    try:
        deadline = time.time() + 5
        addresses = []
        while time.time() < deadline and proc.poll() is None:
            addresses = _listen_addresses(proc.pid)
            if addresses:
                break
            time.sleep(0.05)
        assert "0.0.0.0" not in addresses
        assert "::" not in addresses
        if addresses:
            assert set(addresses) == {"127.0.0.1"}
    finally:
        _stop(proc)


def _snapshot(target):
    loaded = None
    try:
        loaded = model.load_snapshot(target)
    except ImportError:
        loaded = None
    assert loaded is not None, "dashboard.model.load_snapshot is not importable"
    return loaded


def test_r2_same_store(store, cli, resolved_contract, tmp_path, monkeypatch):
    assert SCRIPT.is_file(), f"web launcher missing: {SCRIPT}"
    defs = h.record_defs_by_id(resolved_contract)
    home = tmp_path / "home"
    home_store = home / ".canon" / store.name
    shutil.copytree(store / ".canon", home_store)
    h.create_generic_record(
        cli, defs, "score:effort", subject="local-effort",
        extra_payload={"goal": "local goal", "kind": "deliver"},
    )

    def home_cli(*args):
        return run_cli("--store", str(home_store), *args, root=store)

    h.create_generic_record(
        home_cli, defs, "score:effort", subject="global-effort",
        extra_payload={"goal": "global goal", "kind": "deliver"},
    )
    (store / ".canon" / "store-binding.json").write_text(json.dumps({"store": "global"}))
    monkeypatch.setenv("HOME", str(home))
    target = open_store(store)
    assert target.store_path.resolve() == home_store.resolve()
    snap = _snapshot(target)
    assert [view.effort for view in snap.efforts] == ["global-effort"]

    port = _free_port()
    proc = _spawn(store, ["--port", str(port)], _env(home), tmp_path / "out", tmp_path / "err")
    try:
        status, _content_type, body = _get(port, "/api/snapshot")
        assert 200 <= status < 300, body
        payload = json.loads(body)
        assert [view["effort"] for view in payload["efforts"]] == [view.effort for view in snap.efforts]
        token_status, _token_type, token_body = _get(port, "/api/token")
        assert 200 <= token_status < 300, token_body
        assert json.loads(token_body)["token"] == model.change_token(target)
    finally:
        _stop(proc)


def test_r30_serves_build(store, tmp_path, monkeypatch):
    assert SCRIPT.is_file(), f"web launcher missing: {SCRIPT}"
    page = (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "  <head>\n"
        "    <meta charset=\"UTF-8\" />\n"
        "    <title>Orchestra</title>\n"
        "    <script type=\"module\" crossorigin src=\"/assets/index-webdash.js\"></script>\n"
        "    <link rel=\"stylesheet\" crossorigin href=\"/assets/index-webdash.css\">\n"
        "  </head>\n"
        "  <body>\n"
        "    <div id=\"app\"></div>\n"
        "  </body>\n"
        "</html>\n"
    )
    web_dir = DIST_INDEX.parent.parent
    dist = DIST_INDEX.parent
    made_web = not web_dir.exists()
    made_dist = not dist.exists()
    prior = DIST_INDEX.read_bytes() if DIST_INDEX.is_file() else None
    dist.mkdir(parents=True, exist_ok=True)
    DIST_INDEX.write_text(page)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    port = _free_port()
    proc = None
    try:
        proc = _spawn(store, ["--port", str(port)], _env(tmp_path / "home"), tmp_path / "out", tmp_path / "err")
        try:
            status, content_type, body = _get(port, "/")
        except AssertionError as exc:
            launcher = (tmp_path / "out").read_text() + (tmp_path / "err").read_text()
            raise AssertionError(f"{exc}\nlauncher exit={proc.poll()} output:\n{launcher}") from exc
        assert status == 200, body
        assert "text/html" in content_type
        assert body.decode() == page
        assert body == DIST_INDEX.read_bytes()
    finally:
        _stop(proc)
        if prior is None:
            DIST_INDEX.unlink(missing_ok=True)
        else:
            DIST_INDEX.write_bytes(prior)
        if made_dist:
            shutil.rmtree(dist, ignore_errors=True)
        if made_web and web_dir.exists() and not any(web_dir.iterdir()):
            web_dir.rmdir()
