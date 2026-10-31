"""Characterization of every dashboard endpoint's JSON shape for a seeded store.

Two efforts are seeded: ``alpha`` fills every optional field and ``beta`` leaves them empty.
Each response is normalized (ids, revisions, timestamps, paths) and compared with a
fixture under ``tests/dashboard/fixtures``. Run with ``UPDATE_FIXTURES=1`` to rewrite them.
"""

from __future__ import annotations

import json
import os
import itertools
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

import helpers as h
from conftest import REPO_ROOT, stamped_store

sys.path.insert(0, str(REPO_ROOT))
from orchestra.canon.project import open_store  # noqa: E402
from dashboard.backend.server.app import create_app  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
UPDATE = os.environ.get("UPDATE_FIXTURES") == "1"

RECORD_ID = re.compile(r"rec-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
REVISION = re.compile(r"sha256:[0-9a-f]{64}")
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?")
CHANGE_TOKEN = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
LISTED_TYPES = (
    "score:effort",
    "score:position",
    "score:milestone",
    "score:phase",
    "score:work-item",
    "score:acceptance",
    "score:decision",
    "score:constraint",
    "score:continuity-question",
    "score:specification",
    "score:design",
    "conductor:assignment",
    "conductor:assignment-amendment",
    "conductor:execution-report",
    "conductor:integration-report",
    "conductor:assessment",
    "conductor:proof-packet",
    "conductor:failed-attempt",
    "tuner:check-run",
    "tuner:finding",
    "tuner:investigation-observation",
    "composer:idea",
    "composer:area",
)

SPEC_BODY = (
    "## Requirements\n\n- R1: the list endpoint keeps its shape.\n- R2: the detail endpoint keeps its shape.\n\n"
    "## Acceptance criteria\n\nplaceholder text.\n\n## Constraints\n\nplaceholder text.\n\n"
    "## Non-goals\n\nplaceholder text.\n\n## Invariants\n\nplaceholder text.\n\n## Assumptions\n\nplaceholder text.\n"
)
DESIGN_BODY = "\n\n".join(
    f"## {name}\n\ndesign text for {name}."
    for name in (
        "Architecture",
        "Interfaces",
        "Decisions",
        "Invariants",
        "Assumptions",
        "Tradeoffs",
        "Risks",
    )
)
ASSIGNMENT_BODY = "## Orientation\n\nread the brief first.\n\nextra assignment text."
AMENDMENT_BODY = "## Correction\n\nuse the new fixture name."
PROOF_BODY = "\n\n".join(
    f"## {name}\n\nproof text for {name}." for name in ("Look", "Machine", "Attention", "Diff")
)


STEPPED_CLOCK = """
import datetime as _dt, os, runpy, sys
_real = _dt.datetime
_base = _real(2026, 1, 1, tzinfo=_dt.timezone.utc) + _dt.timedelta(seconds=int(os.environ["SHAPE_CLOCK_STEP"]))
class _Stepped(_real):
    @classmethod
    def now(cls, tz=None):
        return _base if tz is not None else _base.replace(tzinfo=None)
_dt.datetime = _Stepped
sys.argv = ["canon", *sys.argv[1:]]
runpy.run_module("orchestra.canon", run_name="__main__", alter_sys=True)
"""


def _stepped_cli(root: Path) -> Callable[..., subprocess.CompletedProcess]:
    steps = itertools.count()

    def run(*args: str) -> subprocess.CompletedProcess:
        env = {**os.environ, "SHAPE_CLOCK_STEP": str(next(steps))}
        return subprocess.run(
            [sys.executable, "-c", STEPPED_CLOCK, "--root", str(root), *args],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
        )

    return run


@pytest.fixture()
def defs(resolved_contract):
    return h.record_defs_by_id(resolved_contract)


def _create(
    cli, defs, record_type: str, subject: str, payload: dict, body: str | None = None
) -> dict:
    record_def = defs[record_type]
    missing = [name for name in record_def["required"] if name not in payload]
    assert not missing, f"{record_type} {subject} lacks {missing}"
    h.ensure_refs(cli, defs, record_def, payload)
    args = ["create", "--type", record_type, "--subject", subject, "--payload", json.dumps(payload)]
    text = body if body is not None else h.generic_body(record_def)
    if text:
        args.extend(["--body", text])
    result = cli(*args)
    assert result.returncode == 0, (
        f"create {record_type} {subject}: {result.stdout}\n{result.stderr}"
    )
    return json.loads(result.stdout)["record"]


def _phase(cli, defs, effort: str, subject: str, ordinal: int, *states: str, **extra: Any) -> dict:
    record = _create(
        cli,
        defs,
        "score:phase",
        subject,
        {"title": f"title of {subject}", "ordinal": ordinal, "effort": effort, **extra},
    )
    return h.transition(cli, "score:phase", record, *states) if states else record


def _task(cli, defs, effort: str, subject: str, phase: str, **extra: Any) -> dict:
    return _create(
        cli,
        defs,
        "score:work-item",
        subject,
        {
            "title": f"title of {subject}",
            "phase": phase,
            "kind": "deliver",
            "assignee": "",
            "effort": effort,
            **extra,
        },
    )


def _seed_alpha(cli, defs) -> dict[str, str]:
    ids: dict[str, str] = {}
    _create(cli, defs, "score:effort", "alpha", {"goal": "ship alpha", "kind": "deliver"})
    _create(
        cli,
        defs,
        "score:position",
        "alpha",
        {"position": "building the list endpoint", "scope": "effort", "effort": "alpha"},
    )
    _create(
        cli,
        defs,
        "score:milestone",
        "m-first",
        {"title": "first milestone", "ordinal": 1, "effort": "alpha"},
    )
    _phase(cli, defs, "alpha", "p-work", 1, "in_progress", milestone="m-first")
    _phase(cli, defs, "alpha", "route-phase", 2, "in_progress")
    _phase(cli, defs, "alpha", "merge-phase", 3, "in_progress", "done")
    _create(
        cli,
        defs,
        "score:decision",
        "d-one",
        {
            "choice": "keep one reader",
            "alternatives": "two readers",
            "phase": "p-work",
            "effort": "alpha",
        },
    )
    _create(
        cli,
        defs,
        "score:constraint",
        "c-one",
        {"statement": "no new dependencies", "applies_to": "p-work", "effort": "alpha"},
    )
    ids["task"] = _task(
        cli,
        defs,
        "alpha",
        "task-ready",
        "p-work",
        requirements=["R1"],
        decisions=["d-one"],
        size="M",
        estimate_minutes=30,
        attempts=1,
        executor="inline",
    )["id"]
    ids["task_next"] = _task(
        cli,
        defs,
        "alpha",
        "task-next",
        "p-work",
        depends_on=["task-ready"],
        requirements=["R2"],
    )["id"]
    running = _task(cli, defs, "alpha", "task-running", "p-work", executor="subagent")
    h.transition(cli, "score:work-item", running, "in_progress")
    _create(
        cli,
        defs,
        "conductor:assignment",
        "task-running-a1",
        {"work_item": "task-running", "executor": "subagent", "effort": "alpha"},
        ASSIGNMENT_BODY,
    )
    ids["task_running"] = running["id"]
    acceptance = _create(
        cli,
        defs,
        "score:acceptance",
        "task-ready-acc",
        {
            "criterion": "the endpoint keeps its shape",
            "method": "check",
            "phase": "p-work",
            "effort": "alpha",
            "verify_command": "uv run pytest -q",
            "requirement": "R1",
        },
    )
    _create(
        cli,
        defs,
        "tuner:check-run",
        "task-ready-check",
        {
            "criterion_id": acceptance["id"],
            "revision": "abc123",
            "result": "pass",
            "effort": "alpha",
            "method": "check",
            "signed_by": "runner",
            "requirement": "R1",
            "exit_code": 0,
            "duration_s": 1.5,
            "runner": "pytest",
        },
    )
    assignment = _create(
        cli,
        defs,
        "conductor:assignment",
        "task-ready-a1",
        {"work_item": "task-ready", "executor": "subagent", "effort": "alpha"},
        ASSIGNMENT_BODY,
    )
    _create(
        cli,
        defs,
        "conductor:assignment-amendment",
        "task-ready-a1-fix",
        {"assignment": "task-ready-a1", "effort": "alpha"},
        AMENDMENT_BODY,
    )
    _create(
        cli,
        defs,
        "conductor:execution-report",
        "task-ready-report",
        {
            "work_item": "task-ready",
            "assignment": "task-ready-a1",
            "result": "done",
            "verdict": "pass",
            "revision": "abc123",
            "effort": "alpha",
        },
        "report text.",
    )
    _create(
        cli,
        defs,
        "conductor:failed-attempt",
        "task-ready-failed",
        {
            "attempted_action": "run the slow suite",
            "retry_when": "the suite is split",
            "effort": "alpha",
        },
    )
    _create(
        cli,
        defs,
        "tuner:investigation-observation",
        "task-ready-observed",
        {
            "source": "log",
            "observed_time": "today",
            "environment": "ci",
            "what_was_observed": "the shape drifted",
            "effort": "alpha",
        },
    )
    _create(
        cli,
        defs,
        "tuner:finding",
        "task-ready-claim",
        {
            "claim": "the shape is stable",
            "basis": "observed",
            "needs": "none",
            "effort": "alpha",
            "invalidated_when": "a field moves",
            "severity": "low",
        },
    )
    _create(
        cli,
        defs,
        "score:specification",
        "p-work-spec",
        {"weight": "full", "phase": "p-work", "effort": "alpha", "requirements": ["R1", "R2"]},
        SPEC_BODY,
    )
    _create(
        cli,
        defs,
        "score:design",
        "p-work-design",
        {"phase": "p-work", "effort": "alpha", "decisions": ["d-one"]},
        DESIGN_BODY,
    )
    _create(
        cli,
        defs,
        "conductor:assessment",
        "p-work-R1",
        {
            "requirement": "R1",
            "status": "verified",
            "next": "verify",
            "confidence": "high",
            "phase": "p-work",
            "effort": "alpha",
            "level": "implementation",
            "missing": "",
        },
    )
    _create(
        cli,
        defs,
        "conductor:proof-packet",
        "p-work-proof",
        {
            "phase": "p-work",
            "effort": "alpha",
            "revision": "abc123",
            "base": "def456",
            "kind": "mixed",
        },
        PROOF_BODY,
    )
    _create(
        cli,
        defs,
        "score:specification",
        "route-spec",
        {"weight": "light", "phase": "route-phase", "effort": "alpha", "requirements": ["R1"]},
    )
    _create(
        cli,
        defs,
        "conductor:assessment",
        "route-phase-R1",
        {
            "requirement": "R1",
            "phase": "route-phase",
            "effort": "alpha",
            "missing": "",
            "confidence": "high",
            "status": "failed",
            "next": "design",
            "level": "design",
        },
    )
    _create(
        cli,
        defs,
        "conductor:integration-report",
        "route-phase-report",
        {"phase": "route-phase", "effort": "alpha", "result": "fail", "revision": "dirty"},
    )
    _create(
        cli,
        defs,
        "score:continuity-question",
        "alpha",
        {"blocking": True, "scope": "which backend", "owner": "andrew"},
    )
    _create(
        cli,
        defs,
        "score:continuity-question",
        "alpha",
        {"blocking": False, "scope": "port-choice", "owner": "andrew", "question": "pick a port"},
    )
    _create(
        cli,
        defs,
        "tuner:finding",
        "human-finding",
        {
            "claim": "a human must decide",
            "basis": "observed",
            "needs": "human",
            "effort": "alpha",
            "invalidated_when": "decision recorded",
        },
    )
    _create(
        cli,
        defs,
        "tuner:check-run",
        "unsigned-check",
        {
            "criterion_id": acceptance["id"],
            "method": "manual",
            "signed_by": "",
            "result": "pass",
            "effort": "alpha",
            "revision": "abc",
        },
    )
    _create(
        cli,
        defs,
        "composer:idea",
        "park-me",
        {"effort": "alpha", "status": "open", "source": "chat", "phase": "p-work"},
    )
    _create(cli, defs, "composer:idea", "park-too", {"effort": "alpha", "status": "open"})
    ids["assignment"] = assignment["id"]
    ids["acceptance"] = acceptance["id"]
    return ids


def _seed_beta(cli, defs) -> dict[str, str]:
    _create(cli, defs, "score:effort", "beta", {"goal": "ship beta", "kind": "deliver"})
    _phase(cli, defs, "beta", "b-one", 1)
    task = _task(cli, defs, "beta", "b-task", "b-one")
    return {"task": task["id"]}


AREA_SCOPE = "## Scope\n\nInvoices, receipts, and payment flows."


def _seed_areas(cli, defs) -> None:
    _create(cli, defs, "score:effort", "alpha", {"goal": "ship alpha", "kind": "deliver"})
    _create(cli, defs, "composer:area", "billing", {"title": "Billing"}, AREA_SCOPE)
    _create(
        cli,
        defs,
        "composer:area",
        "search",
        {"title": "Search"},
        "## Scope\n\nQuery parsing and ranking.",
    )
    idea = "{}\n".format
    _create(
        cli,
        defs,
        "composer:idea",
        "refund-flow",
        {"status": "open", "area": "billing"},
        idea("Let customers request refunds."),
    )
    _create(
        cli,
        defs,
        "composer:idea",
        "both-ways",
        {"status": "open", "area": "billing", "effort": "alpha", "source": "chat"},
        idea("Show receipts in the backlog and the area."),
    )
    _create(
        cli,
        defs,
        "composer:idea",
        "already-built",
        {"status": "promoted", "area": "billing"},
        idea("Export invoices as PDF."),
    )
    _create(
        cli,
        defs,
        "composer:idea",
        "thrown-out",
        {"status": "dismissed", "area": "billing"},
        idea("Crypto payments."),
    )
    moved = _create(
        cli,
        defs,
        "composer:idea",
        "moved-on",
        {"status": "open", "area": "billing"},
        idea("Retry failed charges."),
    )
    result = cli(
        "supersede",
        "--type",
        "composer:idea",
        "--id",
        moved["id"],
        "--expected-revision",
        "@current",
        "--payload",
        json.dumps({"status": "promoted", "area": "billing"}),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    _create(
        cli,
        defs,
        "composer:idea",
        "typo-tolerance",
        {"status": "open", "area": "search"},
        idea("Forgive typos in queries."),
    )
    _create(
        cli, defs, "composer:idea", "unfiled", {"status": "open"}, idea("Idea without an area.")
    )


def _labels(cli) -> dict[str, str]:
    labels: dict[str, str] = {}
    for record_type in LISTED_TYPES:
        result = cli("list", "--type", record_type)
        assert result.returncode == 0, result.stdout + result.stderr
        for record in json.loads(result.stdout)["records"]:
            label = f"{record_type}:{record['subject']}"
            if record_type == "score:continuity-question":
                label += f":{record['payload']['scope']}"
            assert record["id"] not in labels
            labels[record["id"]] = label
            labels[record["revision"]] = f"rev:{label}"
    return labels


def _build(root: Path, _cli, defs) -> dict[str, Any]:
    cli = _stepped_cli(root)
    alpha = _seed_alpha(cli, defs)
    beta = _seed_beta(cli, defs)
    return {"alpha": alpha, "beta": beta, "labels": _labels(cli)}


def _build_areas(root: Path, _cli, defs) -> dict[str, Any]:
    cli = _stepped_cli(root)
    _seed_areas(cli, defs)
    return {"labels": _labels(cli)}


@pytest.fixture()
def seeded_areas(store, monkeypatch):
    monkeypatch.setenv("ORCHESTRA_SIGNED_BY", "shape-signer")
    seed = stamped_store(store, "endpoint-shapes-areas", _build_areas)
    client = TestClient(create_app(open_store(store)), raise_server_exceptions=False)
    return client, seed, store


@pytest.fixture()
def seeded(store, monkeypatch):
    monkeypatch.setenv("ORCHESTRA_SIGNED_BY", "shape-signer")
    seed = stamped_store(store, "endpoint-shapes", _build)
    client = TestClient(create_app(open_store(store)), raise_server_exceptions=False)
    return client, seed, store


def _normalizer(seed: dict[str, Any], store: Path) -> Callable[[Any], Any]:
    labels: dict[str, str] = seed["labels"]
    store_text = str(store)

    def text(value: str) -> str:
        if CHANGE_TOKEN.match(value):
            return "<token>"
        value = value.replace(store_text, "<store>")
        value = RECORD_ID.sub(lambda m: f"<{labels.get(m.group(0), 'unknown-id')}>", value)
        value = REVISION.sub(lambda m: f"<{labels.get(m.group(0), 'unknown-revision')}>", value)
        return TIMESTAMP.sub("<timestamp>", value)

    def walk(value: Any) -> Any:
        if isinstance(value, dict):
            return {text(str(key)): walk(item) for key, item in value.items()}
        if isinstance(value, list):
            return [walk(item) for item in value]
        if isinstance(value, str):
            return text(value)
        return value

    return walk


def _by_label(seed: dict[str, Any], label: str) -> str:
    matches = [key for key, value in seed["labels"].items() if value == label]
    assert len(matches) == 1, (label, matches)
    return matches[0]


def _record_id(seed: dict[str, Any], record_type: str, subject: str) -> str:
    return _by_label(seed, f"{record_type}:{subject}")


def _revision(seed: dict[str, Any], record_type: str, subject: str) -> str:
    return _by_label(seed, f"rev:{record_type}:{subject}")


def _get(
    path: str, **params: Any
) -> Callable[[dict[str, Any]], tuple[str, str, dict[str, Any], dict | None]]:
    def build(seed):
        resolved = {key: value(seed) if callable(value) else value for key, value in params.items()}
        return "GET", path, resolved, None

    return build


def _needs_body(record_type: str, subject: str, action: str, **extra: Any):
    def build(seed):
        body = {
            "id": _record_id(seed, record_type, subject),
            "action": action,
            "revision": _revision(seed, record_type, subject),
            **extra,
        }
        return "POST", "/api/needs", {}, body

    return build


def _backlog_body(subject: str, action: str):
    def build(seed):
        return (
            "POST",
            "/api/backlog",
            {},
            {"id": _record_id(seed, "composer:idea", subject), "action": action},
        )

    return build


def _id(record_type: str, subject: str):
    return lambda seed: _record_id(seed, record_type, subject)


def _alpha(key: str):
    return lambda seed: seed["alpha"][key]


def _beta(key: str):
    return lambda seed: seed["beta"][key]


CASES: dict[str, Callable[[dict[str, Any]], tuple[str, str, dict[str, Any], dict | None]]] = {
    "token": _get("/api/token"),
    "snapshot": _get("/api/snapshot"),
    "phase-rich": _get("/api/phase", effort="alpha", phase="p-work"),
    "phase-route": _get("/api/phase", effort="alpha", phase="route-phase"),
    "phase-done": _get("/api/phase", effort="alpha", phase="merge-phase"),
    "phase-minimal": _get("/api/phase", effort="beta", phase="b-one"),
    "task-rich": _get("/api/task", id=_alpha("task")),
    "task-dependent": _get("/api/task", id=_alpha("task_next")),
    "task-running": _get("/api/task", id=_alpha("task_running")),
    "task-minimal": _get("/api/task", id=_beta("task")),
    "journal-rich": _get("/api/journal", effort="alpha"),
    "journal-minimal": _get("/api/journal", effort="beta"),
    "record-finding": _get("/api/record", id=_id("tuner:finding", "human-finding")),
    "record-question": _get(
        "/api/record", id=_id("score:continuity-question", "alpha:which backend")
    ),
    "requirement-verified": _get("/api/requirement", effort="alpha", phase="p-work", id="R1"),
    "requirement-unassessed": _get("/api/requirement", effort="alpha", phase="p-work", id="R2"),
    "requirement-failed": _get("/api/requirement", effort="alpha", phase="route-phase", id="R1"),
    "requirement-minimal": _get("/api/requirement", effort="beta", phase="b-one", id="R1"),
    "needs-blocking-question": _get(
        "/api/needs", effort="alpha", id=_id("score:continuity-question", "alpha:which backend")
    ),
    "needs-open-question": _get(
        "/api/needs", effort="alpha", id=_id("score:continuity-question", "alpha:port-choice")
    ),
    "needs-human-finding": _get(
        "/api/needs", effort="alpha", id=_id("tuner:finding", "human-finding")
    ),
    "needs-unsigned-check": _get(
        "/api/needs", effort="alpha", id=_id("tuner:check-run", "unsigned-check")
    ),
    "needs-loop-route": _get(
        "/api/needs", effort="alpha", id=_id("conductor:assessment", "route-phase-R1")
    ),
    "needs-integration": _get(
        "/api/needs", effort="alpha", id=_id("conductor:integration-report", "route-phase-report")
    ),
    "areas-rich": _get("/api/areas"),
    "areas-minimal": _get("/api/areas"),
    "backlog-with-phase": _get("/api/backlog", effort="alpha", id=_id("composer:idea", "park-me")),
    "backlog-without-phase": _get(
        "/api/backlog", effort="alpha", id=_id("composer:idea", "park-too")
    ),
    "post-needs-approve": _needs_body(
        "score:continuity-question", "alpha:which backend", "approve"
    ),
    "post-needs-reject": _needs_body(
        "score:continuity-question", "alpha:port-choice", "reject", note="not now"
    ),
    "post-needs-accept": _needs_body("tuner:finding", "human-finding", "accept", note="agreed"),
    "post-needs-sign": _needs_body("tuner:check-run", "unsigned-check", "sign"),
    "post-backlog-dismiss": _backlog_body("park-me", "dismiss"),
    "post-backlog-promote": _backlog_body("park-too", "promote"),
    "error-task-missing": lambda seed: ("GET", "/api/task", {"id": "rec-missing"}, None),
    "error-phase-missing": _get("/api/phase", effort="alpha", phase="no-such-phase"),
    "error-needs-missing": _get("/api/needs", effort="alpha", id="rec-missing"),
    "error-post-needs-note-required": _needs_body(
        "score:continuity-question", "alpha:port-choice", "reject"
    ),
    "error-post-backlog-action": _backlog_body("park-me", "archive"),
}


def _fixture_path(name: str) -> Path:
    return FIXTURES / f"{name}.json"


def _render(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


@pytest.mark.parametrize("name", sorted(CASES))
def test_endpoint_shape(name, request):
    client, seed, store = request.getfixturevalue(
        "seeded_areas" if name == "areas-rich" else "seeded"
    )
    method, path, params, body = CASES[name](seed)
    response = client.request(method, path, params=params, json=body)
    observed = _normalizer(seed, store)({"status": response.status_code, "body": response.json()})
    rendered = _render(observed)
    target = _fixture_path(name)
    if UPDATE:
        FIXTURES.mkdir(exist_ok=True)
        target.write_text(rendered)
        return
    assert target.is_file(), f"missing fixture {target.name}; run with UPDATE_FIXTURES=1"
    assert rendered == target.read_text()


def test_every_fixture_has_a_case():
    stored = {path.stem for path in FIXTURES.glob("*.json")} if FIXTURES.is_dir() else set()
    assert stored <= set(CASES)


def test_every_route_is_covered(seeded):
    client, seed, _store = seeded
    routes = {
        (method, route.path)
        for route in client.app.routes
        for method in getattr(route, "methods", None) or ()
        if route.path.startswith("/api/") and method in ("GET", "POST")
    }
    covered = {(build(seed)[0], build(seed)[1]) for build in CASES.values()}
    assert routes <= covered


def _plain_create(
    cli, record_type: str, subject: str, payload: dict, body: str | None = None
) -> None:
    args = ["create", "--type", record_type, "--subject", subject, "--payload", json.dumps(payload)]
    if body is not None:
        args.extend(["--body", body])
    result = cli(*args)
    assert result.returncode == 0, (
        f"create {record_type} {subject}: {result.stdout}\n{result.stderr}"
    )


def test_snapshot_effort_carries_area(store, cli):
    for effort in ("placed-effort", "unplaced-effort"):
        _plain_create(cli, "score:effort", effort, {"goal": f"goal of {effort}", "kind": "deliver"})
    _plain_create(cli, "composer:area", "billing", {"title": "Billing"}, AREA_SCOPE)
    _plain_create(cli, "composer:placement", "placed-effort", {"area": "billing"})
    client = TestClient(create_app(open_store(store)), raise_server_exceptions=False)
    response = client.get("/api/snapshot")
    assert response.status_code == 200, response.text
    rows = {row["effort"]: row for row in response.json()["efforts"]}
    assert rows["placed-effort"].get("area") == "billing"
    assert rows["unplaced-effort"].get("area") == ""
