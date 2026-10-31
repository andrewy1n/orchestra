"""Oracles for the areas endpoint and the areas screens of the web dashboard."""

from __future__ import annotations

import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from orchestra.canon.project import open_store  # noqa: E402
from dashboard.backend.server.app import create_app  # noqa: E402

SCRIPT = REPO_ROOT / "dashboard" / "bin" / "web"
UI_SRC = REPO_ROOT / "dashboard" / "frontend" / "src"
SCREENS = UI_SRC / "lib" / "screens"
UV_CACHE_DIR = os.environ.get("UV_CACHE_DIR") or str(Path.home() / ".cache" / "uv")


def _create(cli, record_type: str, subject: str, payload: dict, body: str | None = None) -> dict:
    args = ["create", "--type", record_type, "--subject", subject, "--payload", json.dumps(payload)]
    if body is not None:
        args.extend(["--body", body])
    result = cli(*args)
    assert result.returncode == 0, f"create {record_type} {subject}: {result.stdout}\n{result.stderr}"
    return json.loads(result.stdout)["record"]


def _supersede(cli, record: dict, payload: dict) -> dict:
    result = cli(
        "supersede", "--type", record["record_type"], "--id", record["id"],
        "--expected-revision", "@current", "--payload", json.dumps(payload),
    )
    assert result.returncode == 0, f"supersede {record['subject']}: {result.stdout}\n{result.stderr}"
    return json.loads(result.stdout)["record"]


def _effort(cli, subject: str) -> dict:
    return _create(cli, "score:effort", subject, {"goal": f"goal of {subject}", "kind": "deliver"})


def _area(cli, subject: str, title: str, scope: str) -> dict:
    return _create(cli, "composer:area", subject, {"title": title}, f"## Scope\n\n{scope}\n")


def _idea(cli, subject: str, status: str = "open", text: str | None = None, **refs: str) -> dict:
    return _create(
        cli, "composer:idea", subject, {"status": status, **refs}, f"{text or 'text of ' + subject}\n",
    )


def _client(store: Path) -> TestClient:
    return TestClient(create_app(open_store(store)), raise_server_exceptions=False)


def _areas(store: Path) -> list[dict]:
    response = _client(store).get("/api/areas")
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, list), body
    return body


def _by_subject(items: list[dict]) -> dict[str, dict]:
    return {item["subject"]: item for item in items}


def test_r1_areas_endpoint_lists_every_active_area_with_title_and_scope(store, cli):
    _area(cli, "billing", "Billing", "Invoices and payment flows.")
    _area(cli, "search", "Search", "Query parsing and ranking.")
    areas = _by_subject(_areas(store))
    assert set(areas) == {"billing", "search"}
    assert areas["billing"]["title"] == "Billing"
    assert areas["billing"]["scope"].strip() == "Invoices and payment flows."
    assert areas["search"]["title"] == "Search"
    assert areas["search"]["scope"].strip() == "Query parsing and ranking."


def test_r2_each_area_lists_the_ideas_that_point_at_it(store, cli):
    _area(cli, "billing", "Billing", "Invoices.")
    _area(cli, "search", "Search", "Ranking.")
    _idea(cli, "refund-flow", area="billing")
    _idea(cli, "invoice-pdf", area="billing")
    _idea(cli, "typo-tolerance", area="search")
    _idea(cli, "unfiled")
    areas = _by_subject(_areas(store))
    assert sorted(idea["subject"] for idea in areas["billing"]["ideas"]) == ["invoice-pdf", "refund-flow"]
    assert [idea["subject"] for idea in areas["search"]["ideas"]] == ["typo-tolerance"]


def test_r3_ideas_are_open_or_promoted_and_never_dismissed_or_superseded(store, cli):
    _area(cli, "billing", "Billing", "Invoices.")
    _idea(cli, "still-open", area="billing")
    _idea(cli, "already-promoted", status="promoted", area="billing")
    _idea(cli, "thrown-out", status="dismissed", area="billing")
    moved = _idea(cli, "moved-on", area="billing")
    _supersede(cli, moved, {"status": "promoted", "area": "billing"})
    closed = _idea(cli, "closed-later", area="billing")
    _supersede(cli, closed, {"status": "dismissed", "area": "billing"})
    ideas = _by_subject(_areas(store)[0]["ideas"])
    assert sorted(ideas) == ["already-promoted", "moved-on", "still-open"]
    assert ideas["still-open"]["status"] == "open"
    assert ideas["already-promoted"]["status"] == "promoted"
    assert ideas["moved-on"]["status"] == "promoted"
    listed = [idea["subject"] for idea in _areas(store)[0]["ideas"]]
    assert len(listed) == len(set(listed))


def test_r4_an_idea_with_effort_and_area_shows_in_both_views(store, cli):
    _effort(cli, "alpha")
    _area(cli, "billing", "Billing", "Invoices.")
    _idea(cli, "both-ways", area="billing", effort="alpha")
    client = _client(store)
    snapshot = client.get("/api/snapshot")
    assert snapshot.status_code == 200, snapshot.text
    efforts = {view["effort"]: view for view in snapshot.json()["efforts"]}
    assert [item["subject"] for item in efforts["alpha"]["backlog"]] == ["both-ways"]
    areas = _by_subject(_areas(store))
    assert [idea["subject"] for idea in areas["billing"]["ideas"]] == ["both-ways"]


def test_r5_each_idea_carries_its_area_and_its_effort(store, cli):
    _effort(cli, "alpha")
    _area(cli, "billing", "Billing", "Invoices.")
    _idea(cli, "linked", text="Let customers download receipts.", area="billing", effort="alpha")
    _idea(cli, "area-only", area="billing")
    ideas = _by_subject(_areas(store)[0]["ideas"])
    linked = ideas["linked"]
    assert linked["area"] == "billing"
    assert linked["effort"] == "alpha"
    assert linked["subject"] == "linked"
    assert linked["text"] == "Let customers download receipts."
    assert linked["status"] == "open"
    assert "phase" in linked
    assert ideas["area-only"]["area"] == "billing"
    assert not ideas["area-only"]["effort"]


def test_r11_a_store_without_areas_returns_an_empty_list(store, cli):
    _effort(cli, "alpha")
    _idea(cli, "unfiled", effort="alpha")
    response = _client(store).get("/api/areas")
    assert response.status_code == 200, response.text
    assert response.json() == []


def test_r9_area_screen_has_no_promote_or_dismiss_action():
    screen = SCREENS / "Area.svelte"
    assert screen.is_file(), f"missing {screen}"
    offenders = [
        f"{path.name}: {word}"
        for path in sorted(SCREENS.glob("Area*"))
        if path.is_file()
        for word in ("promote", "dismiss")
        if word in path.read_text().lower()
    ]
    assert not offenders, offenders


def test_r10_router_resolves_an_area_deep_link():
    text = (UI_SRC / "router.ts").read_text()
    assert re.search(r"""["']area["']""", text), "router.ts has no area route name"
    assert re.search(r"area\\?/", text), "router.ts has no /area/ route pattern"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _stop(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=3)


def _get(proc: subprocess.Popen, port: int, path: str, err: Path) -> tuple[int, bytes]:
    url = f"http://127.0.0.1:{port}{path}"
    deadline = time.time() + 120
    last: Exception | None = None
    while time.time() < deadline and proc.poll() is None:
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last = exc
            time.sleep(0.1)
    assert False, f"GET {path} failed (exit {proc.poll()}): {last}\n{err.read_text()}"


def test_web_entry_lists_the_repo_areas(tmp_path, store, cli):
    assert SCRIPT.is_file(), f"web launcher missing: {SCRIPT}"
    assert (REPO_ROOT / ".canon").is_dir(), "the checkout has no .canon store"
    _area(cli, "dashboard", "Dashboard", "The web dashboard.")
    _area(cli, "architecture", "Architecture", "System structure.")
    _area(cli, "agent-slop-standards", "Agent Slop Standards", "Code quality standards.")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env.setdefault("UV_CACHE_DIR", UV_CACHE_DIR)
    env.pop("UV_PYTHON", None)
    env["CANON_STORE"] = str(store / ".canon")
    port = _free_port()
    err = tmp_path / "err"
    with (tmp_path / "out").open("w") as out, err.open("w") as errfile:
        proc = subprocess.Popen(
            [str(SCRIPT), "--port", str(port)], cwd=str(REPO_ROOT), env=env,
            stdout=out, stderr=errfile, text=True, start_new_session=True,
        )
        try:
            status, body = _get(proc, port, "/api/areas", err)
        finally:
            _stop(proc)
    assert status == 200, body
    areas = _by_subject(json.loads(body))
    for subject in ("dashboard", "architecture", "agent-slop-standards"):
        assert subject in areas, f"{subject} missing from {sorted(areas)}"
        assert areas[subject]["title"].strip(), f"{subject} has an empty title"
