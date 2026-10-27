"""The dashboard process uses the orchestra environment.

Modules under dashboard/ open the store with canon.project.open_store.
The process dashboard/bin/dashboard and dashboard/bin/web start must be able to
import that module, because one orchestra dependency covers both trees.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHERS = (
    ROOT / "dashboard" / "bin" / "dashboard",
    ROOT / "dashboard" / "bin" / "web",
)

# Loaded into the launched interpreter via PYTHONPATH. Records whether that
# process can import orchestra.canon.project, then exits before the app.
_PROBE = """
import json
import os
import sys
from pathlib import Path

def _entry(argv0):
    if not argv0 or argv0.startswith("-"):
        return False
    try:
        path = Path(argv0).resolve()
    except OSError:
        return False
    if path.name != "__main__.py":
        return False
    parent = path.parent
    if parent.name == "dashboard":
        return True
    return parent.name == "web" and parent.parent.name == "dashboard"

result = os.environ.get("DASHBOARD_IMPORT_RESULT")
argv0 = sys.argv[0] if sys.argv else ""
if result and _entry(argv0):
    error = ""
    try:
        import orchestra.canon.project
        ok = True
    except Exception as exc:
        ok = False
        error = "%s: %s" % (type(exc).__name__, exc)
    payload = {"ok": ok, "error": error, "executable": sys.executable, "argv0": argv0}
    with open(result, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload))
        handle.flush()
        os.fsync(handle.fileno())
    os._exit(0)
"""


def _repo(path: Path) -> None:
    path.mkdir()
    init = subprocess.run(["git", "init", "-q"], cwd=path, capture_output=True, text=True)
    if init.returncode != 0:
        raise RuntimeError(init.stderr.strip() or "git init failed")
    store = path / ".canon"
    store.mkdir()
    (store / "config.json").write_text(json.dumps({"format": "canon/1", "schemas": {}, "settings": {}}), encoding="utf-8")


def _probe(path: Path) -> None:
    path.mkdir()
    (path / "sitecustomize.py").write_text(_PROBE, encoding="utf-8")


def _launch(launcher: Path, repo: Path, probe: Path, result: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("SE_WORKFLOW_UV", None)
    env.pop("CANON_STORE", None)
    env["PYTHONPATH"] = os.pathsep.join([str(probe), os.environ.get("PYTHONPATH", "")])
    env["DASHBOARD_IMPORT_RESULT"] = str(result)
    return subprocess.run(
        [str(launcher)],
        cwd=repo,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_r2(tmp_path: Path) -> None:
    """R2: the process the dashboard launchers start can import orchestra.canon.project."""
    repo = tmp_path / "repo"
    probe = tmp_path / "probe"
    _repo(repo)
    _probe(probe)

    failures: list[str] = []
    for launcher in LAUNCHERS:
        result = tmp_path / f"{launcher.name}.json"
        try:
            completed = _launch(launcher, repo, probe, result)
        except subprocess.TimeoutExpired:
            assert False, f"{launcher.name} did not exit after starting the dashboard process"
        assert result.is_file(), (
            f"{launcher.name} did not start dashboard/__main__.py "
            f"(exit {completed.returncode}): {completed.stdout} {completed.stderr}"
        )
        payload = json.loads(result.read_text(encoding="utf-8"))
        if not payload["ok"]:
            failures.append(
                f"{launcher.name} via {payload['executable']}: {payload['error']}"
            )

    assert not failures, (
        "dashboard process cannot import orchestra.canon.project\n" + "\n".join(failures)
    )
