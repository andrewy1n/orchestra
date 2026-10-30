from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from orchestra.canon.project import open_store  # noqa: E402
from dashboard.backend.server import app as app_module  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CI = ROOT / ".github" / "workflows" / "ci.yml"
SMOKE = ROOT / "scripts" / "wheel_smoke.py"
FRONTEND = ROOT / "dashboard" / "frontend"
FRONTEND_REL = "dashboard/frontend"
SMOKE_LINE = "python3 scripts/wheel_smoke.py"
EXCLUDED_PARTS = {".git", "node_modules", ".venv", "dist", "__pycache__", ".worktrees", ".canon"}
INDEX_MARKER = "web-packaging-marker-7f3a"


def _jobs():
    yaml = pytest.importorskip("yaml")
    data = yaml.safe_load(CI.read_text())
    assert isinstance(data, dict), "ci.yml is not a mapping"
    return data["jobs"]


def _job(name):
    found = _jobs()
    assert name in found, f"missing job {name}"
    return found[name]


def _run_lines(job):
    lines = []
    for step in job.get("steps", []):
        if "run" in step:
            lines.extend(line.strip() for line in step["run"].splitlines() if line.strip())
    return lines


def _located_lines(job):
    located = []
    for step in job.get("steps", []):
        if "run" not in step:
            continue
        directory = str(step.get("working-directory", "")).strip("./")
        for raw in step["run"].splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.startswith("cd "):
                directory = line[3:].strip().strip("./")
                continue
            located.append((directory, line))
    return located


def _tracked_and_untracked(root: Path) -> list[str]:
    listed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        capture_output=True,
        check=True,
    )
    return [name for name in listed.stdout.decode().split("\0") if name]


def _copy_tree(destination: Path) -> None:
    for name in _tracked_and_untracked(ROOT):
        relative = Path(name)
        if EXCLUDED_PARTS & set(relative.parts):
            continue
        source = ROOT / relative
        if not (source.exists() or source.is_symlink()):
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            os.symlink(os.readlink(source), target)
        else:
            shutil.copy2(source, target)


def _fake_dist(path: Path) -> Path:
    (path / "assets").mkdir(parents=True)
    (path / "index.html").write_text(f"<!doctype html><title>{INDEX_MARKER}</title>")
    (path / "assets" / "app.js").write_text("console.log('app');\n")
    return path


def _smoke(*args: str, timeout: int = 1200) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SMOKE), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_r1_wheel_contains_the_frontend_dist_index(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    _copy_tree(source)
    _fake_dist(source / "dashboard" / "frontend" / "dist")
    env = {k: v for k, v in os.environ.items() if k not in {"VIRTUAL_ENV", "PYTHONPATH"}}
    built = subprocess.run(
        ["uv", "build", "--wheel"],
        cwd=source,
        env=env,
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    wheels = sorted((source / "dist").glob("*.whl"))
    assert len(wheels) == 1, [path.name for path in wheels]
    with zipfile.ZipFile(wheels[0]) as archive:
        names = set(archive.namelist())
    assert "dashboard/frontend/dist/index.html" in names
    assert "dashboard/frontend/dist/assets/app.js" in names


def test_r2_wheel_job_builds_the_frontend_before_the_smoke_script():
    located = _located_lines(_job("wheel"))
    smoke = [i for i, (_, line) in enumerate(located) if line == SMOKE_LINE]
    assert smoke, "wheel job does not run the smoke script"
    builds = [
        i for i, (directory, line) in enumerate(located)
        if line == "npm run build" and directory == FRONTEND_REL
    ]
    assert builds, f"wheel job has no `npm run build` in {FRONTEND_REL}"
    assert builds[0] < smoke[0]


def test_r3_dist_is_gitignored_and_untracked():
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "dashboard/frontend/dist/index.html"],
        cwd=ROOT,
    )
    assert ignored.returncode == 0
    tracked = subprocess.run(
        ["git", "ls-files", "dashboard/frontend/dist"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert tracked.stdout.strip() == ""


def test_r4_installed_wheel_serves_the_index_at_root(tmp_path):
    dist = _fake_dist(tmp_path / "dist")
    result = _smoke("--dist", str(dist))
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "GET /: pass" in result.stdout.splitlines(), output


def test_r4_missing_dist_fails_and_names_the_build_command(tmp_path):
    empty = tmp_path / "empty-dist"
    empty.mkdir()
    result = _smoke("--dist", str(empty))
    output = result.stdout + result.stderr
    assert result.returncode == 1, output
    assert "npm run build" in output


def test_r5_wheel_job_sets_up_node_and_the_script_checks_the_root():
    wheel = _job("wheel")
    uses = [str(step.get("uses", "")) for step in wheel.get("steps", [])]
    assert any(item.startswith("actions/setup-node") for item in uses)
    assert _run_lines(wheel).count(SMOKE_LINE) == 1
    assert "GET /" in SMOKE.read_text()


def test_r6_playwright_test_starts_the_server_and_loads_the_page():
    package = json.loads((FRONTEND / "package.json").read_text())
    version = package.get("devDependencies", {}).get("@playwright/test", "")
    assert re.fullmatch(r"\d+\.\d+\.\d+", version), f"@playwright/test version {version!r} is not exact"
    assert "playwright test" in package.get("scripts", {}).get("e2e", "")
    config = FRONTEND / "playwright.config.ts"
    assert config.is_file(), "missing playwright.config.ts"
    assert "chromium" in config.read_text()
    spec = FRONTEND / "e2e" / "app.spec.ts"
    assert spec.is_file(), "missing e2e/app.spec.ts"
    assert "page.goto" in spec.read_text()
    assert (FRONTEND / "e2e" / "serve.py").is_file(), "missing e2e/serve.py"


def test_r7_playwright_test_asserts_a_seeded_effort_name():
    spec = FRONTEND / "e2e" / "app.spec.ts"
    serve = FRONTEND / "e2e" / "serve.py"
    assert spec.is_file(), "missing e2e/app.spec.ts"
    assert serve.is_file(), "missing e2e/serve.py"
    text = spec.read_text()
    assert "toBeVisible" in text
    assert "e2e-alpha" in text
    assert "e2e-alpha" in serve.read_text()


def test_r8_ci_job_installs_the_browser_and_runs_the_playwright_test():
    names = [name for name in _jobs() if "e2e" in name]
    assert names, "no job with e2e in its key"
    job = _jobs()[names[0]]
    lines = _run_lines(job)
    assert any("playwright install" in line and "chromium" in line for line in lines)
    assert "npm run e2e" in lines
    assert "continue-on-error" not in job
    assert not any("continue-on-error" in step for step in job.get("steps", []))


def test_r9_missing_build_message_names_the_build_command(store, monkeypatch, tmp_path):
    monkeypatch.setattr(app_module, "DIST", tmp_path / "no-dist")
    client = TestClient(app_module.create_app(open_store(store)), raise_server_exceptions=False)
    response = client.get("/")
    assert response.status_code == 200
    assert "npm run build" in response.text
    assert "dashboard/frontend" in response.text
