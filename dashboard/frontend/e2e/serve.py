from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

from orchestra.canon.git_backend import run_git

REPO_ROOT = Path(__file__).resolve().parents[3]
EFFORT = "e2e-alpha"
PHASE = "e2e-phase"
TASK = "e2e-task"
AREA = "e2e-area"
PHASE_SECTIONS = ("Problem", "Approach", "Exit criteria")
AREA_SECTIONS = ("Scope",)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def check(result: subprocess.CompletedProcess[str]) -> None:
    if result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit(result.returncode)


def run(command: list[str], cwd: Path, env: dict[str, str]) -> None:
    check(subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True))


def seed(store_root: Path, env: dict[str, str]) -> None:
    for args in (
        ("init", "-q"),
        ("config", "user.email", "e2e@example.com"),
        ("config", "user.name", "e2e"),
        ("commit", "--allow-empty", "-qm", "init"),
    ):
        check(run_git(store_root, *args, env=env, capture_output=True, text=True))
    canon = [sys.executable, "-m", "orchestra.canon", "--root", str(store_root)]

    def create(
        record_type: str, subject: str, payload: dict[str, object], sections: tuple[str, ...] = ()
    ) -> None:
        command = [
            *canon,
            "create",
            "--type",
            record_type,
            "--subject",
            subject,
            "--payload",
            json.dumps(payload),
        ]
        if sections:
            body = "\n\n".join(f"## {name}\n\nE2E {name}." for name in sections)
            command.extend(["--body", body])
        run(command, REPO_ROOT, env)

    run([*canon, "init", "--schemas", "score,conductor,tuner,composer"], REPO_ROOT, env)
    create("composer:area", AREA, {"title": "E2E area"}, AREA_SECTIONS)
    create("score:effort", EFFORT, {"goal": "Exercise the packaged dashboard", "kind": "deliver"})
    create("composer:placement", EFFORT, {"area": AREA})
    create(
        "score:phase", PHASE, {"title": "E2E phase", "ordinal": 1, "effort": EFFORT}, PHASE_SECTIONS
    )
    create(
        "score:work-item",
        TASK,
        {
            "title": "E2E task",
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "attempts": 0,
            "estimate_minutes": 0,
        },
        ("Description",),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the dashboard on a seeded temporary store")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    port = args.port or free_port()

    env = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(
            filter(None, [str(REPO_ROOT), os.environ.get("PYTHONPATH", "")])
        ),
    }
    store_root = Path(tempfile.mkdtemp(prefix="dashboard-e2e-"))
    server: subprocess.Popen[bytes] | None = None

    def stop(_signum: int, _frame: object) -> None:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        seed(store_root, env)
        server = subprocess.Popen(
            [sys.executable, "-m", "dashboard.backend.server", "--port", str(port)],
            cwd=store_root,
            env=env,
        )
        print(f"http://127.0.0.1:{port}", flush=True)
        return server.wait()
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
        shutil.rmtree(store_root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
