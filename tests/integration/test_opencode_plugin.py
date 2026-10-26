"""Integration: the installed OpenCode plugin loads and receives events.

This drives a real ``opencode serve`` process against a temporary HOME. The
installer writes the plugin to the global OpenCode config root, the server
loads it, and creating/removing a session must run the fake
``orchestra`` hook commands in the project directory.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENCODE = shutil.which("opencode")

pytestmark = pytest.mark.skipif(
    OPENCODE is None, reason="opencode is not installed"
)

FAKE_HOOK = """#!/bin/sh
printf '%s %s\\n' "$1" "$PWD" >> "$ORCHESTRA_HOOK_LOG"
exit 0
"""


def run_install(home: Path, project: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(REPO_ROOT), env.get("PYTHONPATH", "")]
    ).strip(os.pathsep)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "orchestra.cli",
            "install",
            "--only",
            "opencode",
            "--global",
            "--copy",
            "--home",
            str(home),
        ],
        cwd=str(project),
        env=env,
        capture_output=True,
        text=True,
    )


def wait_for(path: Path, needles: tuple[str, ...], timeout: float = 15.0) -> str:
    deadline = time.monotonic() + timeout
    text = ""
    while time.monotonic() < deadline:
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            if all(needle in text for needle in needles):
                return text
        time.sleep(0.1)
    raise AssertionError(
        f"timed out waiting for {needles!r} in {path}:\n{text[-4000:]}"
    )


def api(
    opencode: str,
    env: dict[str, str],
    url: str,
    password: str,
    *args: str,
) -> subprocess.CompletedProcess:
    command_env = dict(env)
    command_env["OPENCODE_PASSWORD"] = password
    return subprocess.run(
        [opencode, "api", "--server", url, *args],
        env=command_env,
        capture_output=True,
        text=True,
    )


def test_installed_opencode_plugin_loads_and_emits_hooks(tmp_path: Path):
    version = subprocess.run(
        [OPENCODE, "--version"], capture_output=True, text=True
    )
    match = re.search(r"(?:^|\s)v?(\d+)\.\d+\.\d+", version.stdout)
    if not match or match.group(1) != "2":
        pytest.skip("this test requires OpenCode V2")

    home = tmp_path / "home"
    project = tmp_path / "project"
    fake_bin = tmp_path / "bin"
    project.mkdir()
    fake_bin.mkdir()
    hook_log = tmp_path / "hooks.log"
    server_log = tmp_path / "opencode.log"

    installed = run_install(home, project)
    assert installed.returncode == 0, installed.stdout + installed.stderr
    plugin = home / ".config" / "opencode" / "plugins" / "plugin.js"
    assert plugin.is_file()

    hook = fake_bin / "orchestra"
    hook.write_text(FAKE_HOOK, encoding="utf-8")
    hook.chmod(0o755)

    env = dict(os.environ)
    env["HOME"] = str(home)
    env["XDG_CONFIG_HOME"] = str(home / ".config")
    env["ORCHESTRA_HOOK_LOG"] = str(hook_log)
    env["PATH"] = os.pathsep.join([str(fake_bin), env.get("PATH", "")])

    with server_log.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [OPENCODE, "serve", "--port", "0", "--print-logs"],
            cwd=str(project),
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    try:
        text = wait_for(
            server_log,
            ("server listening on http://", "server password "),
        )
        url = re.search(r"server listening on (http://\S+)", text).group(1)
        password = re.search(r"server password (\S+)", text).group(1)

        # Booting a location loads its plugins. Wait for that to finish before
        # creating a session so the plugin cannot miss session.created.
        ready = api(OPENCODE, env, url, password, "GET", "/api/plugin")
        assert ready.returncode == 0, ready.stdout + ready.stderr

        created = api(
            OPENCODE,
            env,
            url,
            password,
            "-d",
            '{"title":"plugin integration"}',
            "POST",
            "/api/session",
        )
        assert created.returncode == 0, created.stdout + created.stderr
        session = json.loads(created.stdout)["data"]
        assert session["location"]["directory"] == str(project), session
        wait_for(hook_log, (f"hook-start {project}",))

        deleted = api(
            OPENCODE,
            env,
            url,
            password,
            "DELETE",
            f"/api/session/{session['id']}",
        )
        assert deleted.returncode == 0, deleted.stdout + deleted.stderr
        wait_for(hook_log, (f"hook-stop {project}",))

        log_text = server_log.read_text(encoding="utf-8", errors="replace")
        assert "failed to load plugin" not in log_text
        assert str(plugin) in log_text
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
