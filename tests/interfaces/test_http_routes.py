from __future__ import annotations

import json
import re
import shutil
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from helpers import generic_body, schema_defs

from dashboard.backend.server.app import create_app
from interfaces.interfaces_support import build_store, run_cli
from orchestra.canon.project import open_store

RECORD_ID = re.compile(r"rec-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
REVISION = re.compile(r"sha256:[0-9a-f]{64}")
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?")
ELAPSED = re.compile(r"\d+ (?:day|hour|minute|second)s? ago")
CHANGE_TOKEN = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")

SPEC_BODY = (
    "## Requirements\n\n- R1: the route keeps its body.\n\n"
    + "\n\n".join(
        f"## {name}\n\nplaceholder text."
        for name in (
            "Acceptance criteria",
            "Constraints",
            "Non-goals",
            "Invariants",
            "Assumptions",
        )
    )
    + "\n"
)

LISTED_TYPES = (
    "score:effort",
    "score:phase",
    "score:work-item",
    "score:acceptance",
    "score:specification",
    "score:continuity-question",
    "tuner:check-run",
    "tuner:finding",
    "composer:idea",
    "composer:area",
)

Seed = dict[str, str]


def _create(
    root: Path, record_type: str, subject: str, payload: dict[str, object], body: str = ""
) -> None:
    args = ["create", "--type", record_type, "--subject", subject, "--payload", json.dumps(payload)]
    text = body or generic_body(schema_defs()[record_type])
    if text:
        args.extend(["--body", text])
    result = run_cli(*args, root=root)
    assert result.returncode == 0, result.stdout + result.stderr


def _ids(root: Path) -> Seed:
    labels: Seed = {}
    for record_type in LISTED_TYPES:
        result = run_cli("list", "--type", record_type, root=root)
        assert result.returncode == 0, result.stdout + result.stderr
        for record in json.loads(result.stdout)["records"]:
            label = f"{record_type}:{record['subject']}"
            if record_type == "score:continuity-question":
                label += f":{record['payload']['scope']}"
            labels[record["id"]] = label
            labels[record["revision"]] = f"rev:{label}"
    return labels


def _wait_for_next_second() -> None:
    start = int(time.time())
    while int(time.time()) == start:
        time.sleep(0.05)


def _seed(root: Path) -> None:
    _create(root, "score:effort", "alpha", {"goal": "ship alpha", "kind": "deliver"})
    _create(
        root,
        "score:phase",
        "p-one",
        {"title": "first phase", "ordinal": 1, "effort": "alpha"},
    )
    phase = json.loads(run_cli("list", "--type", "score:phase", root=root).stdout)["records"][0]
    transition = run_cli(
        "update",
        "--type",
        "score:phase",
        "--id",
        phase["id"],
        "--transition",
        "in_progress",
        "--expected-revision",
        phase["revision"],
        root=root,
    )
    assert transition.returncode == 0, transition.stdout + transition.stderr
    _create(
        root,
        "score:work-item",
        "t-one",
        {
            "title": "first task",
            "phase": "p-one",
            "kind": "deliver",
            "assignee": "",
            "effort": "alpha",
            "requirements": ["R1"],
        },
    )
    _create(
        root,
        "score:specification",
        "p-one-spec",
        {"weight": "full", "phase": "p-one", "effort": "alpha", "requirements": ["R1"]},
        SPEC_BODY,
    )
    _create(
        root,
        "score:acceptance",
        "t-one-acc",
        {
            "criterion": "the route keeps its body",
            "method": "check",
            "phase": "p-one",
            "effort": "alpha",
            "verify_command": "uv run pytest -q",
            "requirement": "R1",
        },
    )
    acceptance = json.loads(run_cli("list", "--type", "score:acceptance", root=root).stdout)[
        "records"
    ][0]
    _create(
        root,
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
        root,
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
    _wait_for_next_second()
    _create(
        root,
        "score:continuity-question",
        "alpha",
        {"blocking": False, "scope": "port-choice", "owner": "andrew", "question": "pick a port"},
    )
    _create(root, "composer:area", "billing", {"title": "Billing"}, "## Scope\n\nInvoices.")
    _create(
        root,
        "composer:idea",
        "park-me",
        {
            "effort": "alpha",
            "status": "open",
            "source": "chat",
            "phase": "p-one",
            "area": "billing",
        },
        "Park this idea.\n",
    )


@pytest.fixture(scope="module")
def served() -> Iterator[tuple[TestClient, Seed, Path]]:
    root = build_store()
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("ORCHESTRA_SIGNED_BY", "route-signer")
        try:
            _seed(root)
            labels = _ids(root)
            client = TestClient(create_app(open_store(root)), raise_server_exceptions=False)
            yield client, labels, root
        finally:
            shutil.rmtree(root, ignore_errors=True)


def _normalizer(labels: Seed, root: Path) -> Callable[[object], object]:
    def text(value: str) -> str:
        if CHANGE_TOKEN.match(value):
            return "<token>"
        value = value.replace(str(root), "<store>")
        value = RECORD_ID.sub(lambda m: f"<{labels.get(m.group(0), 'unknown-id')}>", value)
        value = REVISION.sub(lambda m: f"<{labels.get(m.group(0), 'unknown-revision')}>", value)
        return ELAPSED.sub("<elapsed>", TIMESTAMP.sub("<timestamp>", value))

    def walk(value: object) -> object:
        if isinstance(value, dict):
            return {text(str(key)): walk(item) for key, item in value.items()}
        if isinstance(value, list):
            return [walk(item) for item in value]
        if isinstance(value, str):
            return text(value)
        return value

    return walk


def _id_of(labels: Seed, label: str) -> str:
    matches = [key for key, value in labels.items() if value == label]
    assert len(matches) == 1, (label, matches)
    return matches[0]


CASES: dict[str, tuple[str, Callable[[Seed], dict[str, str]]]] = {
    "token": ("/api/token", lambda _l: {}),
    "snapshot": ("/api/snapshot", lambda _l: {}),
    "areas": ("/api/areas", lambda _l: {}),
    "product": ("/api/product", lambda _l: {}),
    "hub": ("/api/hub", lambda _l: {}),
    "phase": ("/api/phase", lambda _l: {"effort": "alpha", "phase": "p-one"}),
    "task": ("/api/task", lambda labels: {"id": _id_of(labels, "score:work-item:t-one")}),
    "journal": ("/api/journal", lambda _l: {"effort": "alpha"}),
    "record": ("/api/record", lambda labels: {"id": _id_of(labels, "tuner:finding:human-finding")}),
    "requirement": (
        "/api/requirement",
        lambda _l: {"effort": "alpha", "phase": "p-one", "id": "R1"},
    ),
    "needs": (
        "/api/needs",
        lambda labels: {"effort": "alpha", "id": _id_of(labels, "tuner:finding:human-finding")},
    ),
    "backlog": (
        "/api/backlog",
        lambda labels: {"effort": "alpha", "id": _id_of(labels, "composer:idea:park-me")},
    ),
    "error-task-unknown": ("/api/task", lambda _l: {"id": "rec-missing"}),
    "error-phase-unknown": ("/api/phase", lambda _l: {"effort": "alpha", "phase": "no-such-phase"}),
    "error-record-unknown": ("/api/record", lambda _l: {"id": "rec-missing"}),
    "journal-unknown-effort": ("/api/journal", lambda _l: {"effort": "no-such-effort"}),
    "requirement-unknown-phase": (
        "/api/requirement",
        lambda _l: {"effort": "alpha", "phase": "no-such-phase", "id": "R1"},
    ),
    "error-needs-unknown": ("/api/needs", lambda _l: {"effort": "alpha", "id": "rec-missing"}),
    "error-backlog-unknown": ("/api/backlog", lambda _l: {"effort": "alpha", "id": "rec-missing"}),
    "error-phase-missing-param": ("/api/phase", lambda _l: {"effort": "alpha"}),
}

EXPECTED: dict[str, object] = json.loads(
    (
        Path(__file__).resolve().parents[2]
        / "dashboard/frontend/src/testing/fixtures/http_pins.json"
    ).read_text(encoding="utf-8")
)


@pytest.mark.parametrize("name", sorted(CASES))
def test_get_route_matches_recorded_response(
    name: str, served: tuple[TestClient, Seed, Path]
) -> None:
    client, labels, root = served
    path, params = CASES[name]
    response = client.get(path, params=params(labels))
    observed = _normalizer(labels, root)({"status": response.status_code, "body": response.json()})
    assert observed == EXPECTED[name]


def test_every_get_route_has_a_case(served: tuple[TestClient, Seed, Path]) -> None:
    _client, _labels, root = served
    routes = {
        route.path
        for route in create_app(open_store(root)).routes
        if isinstance(route, APIRoute)
        and route.path.startswith("/api/")
        and "GET" in (route.methods or set())
    }
    assert routes <= {path for path, _params in CASES.values()}


def _transition(root: Path, record_type: str, subject: str, state: str) -> None:
    record = next(
        item
        for item in json.loads(run_cli("list", "--type", record_type, root=root).stdout)["records"]
        if item["subject"] == subject
    )
    result = run_cli(
        "update",
        "--type",
        record_type,
        "--id",
        record["id"],
        "--transition",
        state,
        "--expected-revision",
        record["revision"],
        root=root,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _seed_phase_rows(root: Path) -> None:
    _create(root, "score:effort", "alpha", {"goal": "ship alpha", "kind": "deliver"})
    _create(
        root,
        "score:milestone",
        "m-one",
        {"title": "Milestone one", "ordinal": 2, "effort": "alpha"},
    )
    _create(
        root,
        "score:milestone",
        "m-two",
        {"title": "Milestone two", "ordinal": 1, "effort": "alpha"},
    )
    _create(root, "score:milestone", "m-empty", {"title": "Empty", "ordinal": 3, "effort": "alpha"})
    _create(
        root, "score:milestone", "m-done", {"title": "Shipped", "ordinal": 4, "effort": "alpha"}
    )
    phases = (
        ("p-live", 1, "m-one"),
        ("p-done", 2, "m-done"),
        ("p-plain", 3, None),
        ("p-wait", 4, "m-two"),
    )
    for subject, ordinal, milestone in phases:
        payload: dict[str, object] = {"title": subject, "ordinal": ordinal, "effort": "alpha"}
        if milestone:
            payload["milestone"] = milestone
        _create(root, "score:phase", subject, payload)
        _transition(root, "score:phase", subject, "in_progress")
    tasks = (
        ("live-a", "p-live", "inline", 10),
        ("live-b", "p-live", "inline", 15),
        ("live-c", "p-live", "inline", None),
        ("wait-a", "p-wait", "subagent", 40),
        ("plain-a", "p-plain", "subagent", 0),
        ("plain-b", "p-plain", "subagent", 30),
    )
    for subject, phase, executor, estimate in tasks:
        payload = {
            "title": subject,
            "phase": phase,
            "kind": "deliver",
            "assignee": "",
            "effort": "alpha",
            "executor": executor,
        }
        if estimate is not None:
            payload["estimate_minutes"] = estimate
        _create(root, "score:work-item", subject, payload)
    _create(
        root,
        "score:work-item",
        "done-a",
        {
            "title": "done-a",
            "phase": "p-done",
            "kind": "deliver",
            "assignee": "",
            "effort": "alpha",
        },
    )
    for state in ("in_progress", "done"):
        _transition(root, "score:work-item", "done-a", state)
    _transition(root, "score:phase", "p-done", "done")
    for subject, acceptance_phase in (("wait-a", "p-wait"), ("live-a", "p-live")):
        _create(
            root,
            "score:acceptance",
            f"{subject}-acc",
            {
                "criterion": "signed off by a person",
                "method": "manual",
                "phase": acceptance_phase,
                "effort": "alpha",
                "verify_command": "true",
                "requirement": "R1",
            },
        )
    acceptances = {
        item["subject"]: item["id"]
        for item in json.loads(run_cli("list", "--type", "score:acceptance", root=root).stdout)[
            "records"
        ]
    }
    _create(
        root,
        "tuner:check-run",
        "wait-a-run",
        {
            "criterion_id": acceptances["wait-a-acc"],
            "method": "manual",
            "signed_by": "",
            "result": "pass",
            "effort": "alpha",
            "revision": "abc",
        },
    )
    _create(
        root,
        "tuner:check-run",
        "p-live-suite",
        {
            "criterion_id": "suite",
            "method": "check",
            "signed_by": "",
            "result": "pass",
            "effort": "alpha",
            "revision": "abcdef0123456789",
            "evidence_kind": "integration",
        },
    )
    _create(
        root,
        "tuner:check-run",
        "p-plain-tier2",
        {
            "criterion_id": "suite",
            "method": "check",
            "signed_by": "",
            "result": "fail",
            "effort": "alpha",
            "revision": "deadbeef0000",
            "evidence_kind": "integration",
        },
    )
    _create(
        root,
        "tuner:check-run",
        "p-wait-suite",
        {
            "criterion_id": "suite",
            "method": "check",
            "signed_by": "",
            "result": "blocked",
            "effort": "alpha",
            "revision": "1234567890ab",
            "evidence_kind": "integration",
        },
        "suite-running in worktree",
    )


PHASE_ROW_FIELDS = (
    "subject",
    "title",
    "ordinal",
    "state",
    "done",
    "total",
    "in_progress",
    "awaiting_signoff",
    "elapsed_minutes",
    "unset_estimates",
    "suite",
    "milestone",
    "milestone_title",
)


def _phase_row(
    subject: str,
    ordinal: int,
    state: str,
    done: int,
    total: int,
    awaiting_signoff: bool,
    elapsed_minutes: int | None,
    unset_estimates: int,
    suite: str,
    milestone: str,
    milestone_title: str,
) -> dict[str, object]:
    return {
        "subject": subject,
        "title": subject,
        "ordinal": ordinal,
        "state": state,
        "done": done,
        "total": total,
        "in_progress": [],
        "awaiting_signoff": awaiting_signoff,
        "elapsed_minutes": elapsed_minutes,
        "unset_estimates": unset_estimates,
        "suite": suite,
        "milestone": milestone,
        "milestone_title": milestone_title,
    }


PHASE_ROWS_EXPECTED = [
    _phase_row("p-plain", 3, "in_progress", 0, 2, False, 30, 0, "suite fail@deadbee", "", ""),
    _phase_row(
        "p-wait", 4, "in_progress", 0, 1, True, 40, 0, "suite running", "m-two", "Milestone two"
    ),
    _phase_row(
        "p-live", 1, "in_progress", 0, 3, False, 25, 1, "suite ok@abcdef0", "m-one", "Milestone one"
    ),
    _phase_row("p-done", 2, "done", 1, 1, False, None, 1, "", "m-done", "Shipped"),
]

MILESTONE_ROWS_EXPECTED = [
    {
        "subject": "m-two",
        "title": "Milestone two",
        "ordinal": 1,
        "state": "in_progress",
        "done": 0,
        "total": 1,
    },
    {
        "subject": "m-one",
        "title": "Milestone one",
        "ordinal": 2,
        "state": "in_progress",
        "done": 0,
        "total": 1,
    },
    {
        "subject": "m-empty",
        "title": "Empty",
        "ordinal": 3,
        "state": "planned",
        "done": 0,
        "total": 0,
    },
    {"subject": "m-done", "title": "Shipped", "ordinal": 4, "state": "done", "done": 1, "total": 1},
]


def test_phase_rows_and_milestones_route_pins() -> None:
    root = build_store()
    try:
        with pytest.MonkeyPatch.context() as patch:
            patch.setenv("ORCHESTRA_SIGNED_BY", "route-signer")
            _seed_phase_rows(root)
            client = TestClient(create_app(open_store(root)), raise_server_exceptions=False)
            response = client.get("/api/snapshot")
        assert response.status_code == 200, response.text
        effort = next(item for item in response.json()["efforts"] if item["effort"] == "alpha")
        phases = [{key: row[key] for key in PHASE_ROW_FIELDS} for row in effort["phases"]]
        milestones = [
            {key: row[key] for key in ("subject", "title", "ordinal", "state", "done", "total")}
            for row in effort["milestones"]
        ]
        assert phases == PHASE_ROWS_EXPECTED
        assert milestones == MILESTONE_ROWS_EXPECTED
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _spec_body(texts: dict[str, str]) -> str:
    lines = "\n".join(f"{rid}: {text}" for rid, text in texts.items())
    sections = "\n\n".join(
        f"## {name}\n\n{'keep display only.' if name == 'Non-goals' else 'placeholder text.'}"
        for name in ("Acceptance criteria", "Constraints", "Non-goals", "Invariants", "Assumptions")
    )
    return f"## Requirements\n\n{lines}\n\n{sections}\n"


LIGHT_PHASE_BODY = (
    "## Problem\n\np.\n\n## Approach\n\na.\n\n## Exit criteria\n\ne.\n\n"
    "## Requirements\n\nR1: light one.\nR2: light two.\n"
)


def _acceptance_ids(root: Path) -> dict[str, str]:
    listed = json.loads(run_cli("list", "--type", "score:acceptance", root=root).stdout)["records"]
    return {item["subject"]: item["id"] for item in listed}


def _evidence_acceptance(root: Path, subject: str, phase: str, payload: dict[str, object]) -> None:
    _create(
        root,
        "score:acceptance",
        subject,
        {
            "criterion": f"{subject} holds",
            "method": "check",
            "phase": phase,
            "effort": "alpha",
            "verify_command": "true",
            **payload,
        },
    )


def _evidence_check(
    root: Path, subject: str, criterion: str, result: str, extra: dict[str, object] | None = None
) -> None:
    _create(
        root,
        "tuner:check-run",
        subject,
        {
            "criterion_id": criterion,
            "method": "check",
            "signed_by": "",
            "result": result,
            "effort": "alpha",
            "revision": "abc",
            **(extra or {}),
        },
    )


def _evidence_assessment(root: Path, subject: str, requirement: str, status: str, nxt: str) -> None:
    _create(
        root,
        "conductor:assessment",
        subject,
        {
            "phase": "ev-full",
            "effort": "alpha",
            "requirement": requirement,
            "status": status,
            "next": nxt,
            "confidence": "low" if status == "failed" else "high",
            "level": "design",
        },
    )


def _seed_phase_evidence(root: Path) -> None:
    _create(root, "score:effort", "alpha", {"goal": "ship alpha", "kind": "deliver"})
    phases: tuple[tuple[str, int, dict[str, object], str], ...] = (
        ("ev-full", 1, {}, ""),
        ("ev-light", 2, {"weight": "light"}, LIGHT_PHASE_BODY),
        ("ev-other", 3, {}, ""),
    )
    for subject, ordinal, payload, body in phases:
        _create(
            root,
            "score:phase",
            subject,
            {"title": subject, "ordinal": ordinal, "effort": "alpha", **payload},
            body,
        )
        _transition(root, "score:phase", subject, "in_progress")
    _create(
        root,
        "score:specification",
        "ev-full-spec",
        {
            "weight": "full",
            "phase": "ev-full",
            "effort": "alpha",
            "requirements": ["R1", "R2", "R3"],
        },
        _spec_body({"R1": "first text.", "R2": "second text.", "R3": "third text."}),
    )
    for subject, choice in (("d-one", "use owners"), ("d-two", "keep routes")):
        _create(
            root,
            "score:decision",
            subject,
            {"choice": choice, "alternatives": "none", "phase": "ev-full", "effort": "alpha"},
        )
    _create(
        root,
        "score:design",
        "ev-full-design",
        {"phase": "ev-full", "effort": "alpha", "decisions": ["d-one", "d-two"]},
    )
    for subject, phase, requirements, done in (
        ("t-a", "ev-full", ["R1", "R1", "R2"], True),
        ("t-b", "ev-full", ["R1"], False),
        ("t-c", "ev-other", ["R1"], False),
        ("t-d", "ev-light", ["R1"], True),
    ):
        payload: dict[str, object] = {
            "title": subject,
            "phase": phase,
            "kind": "deliver",
            "assignee": "",
            "effort": "alpha",
            "requirements": requirements,
        }
        if subject == "t-a":
            payload["decisions"] = ["d-two", "d-one"]
        _create(root, "score:work-item", subject, payload)
        if done:
            _transition(root, "score:work-item", subject, "in_progress")
            _transition(root, "score:work-item", subject, "done")
    _evidence_acceptance(root, "a-r1", "ev-full", {"requirement": "R1"})
    _evidence_acceptance(root, "a-r2", "ev-full", {"requirements": ["R2", "R3"]})
    _evidence_acceptance(root, "a-light", "ev-light", {"requirement": "R1"})
    _evidence_acceptance(root, "a-other", "ev-other", {"requirement": "R1"})
    ids = _acceptance_ids(root)
    _evidence_check(
        root, "run-r1", ids["a-r1"], "pass", {"requirement": "R1", "evidence_kind": "unit"}
    )
    _evidence_check(root, "run-r2", ids["a-r2"], "pass")
    _evidence_check(root, "run-light", ids["a-light"], "pass")
    _evidence_check(root, "run-other", ids["a-other"], "fail")
    _wait_for_next_second()
    _evidence_assessment(root, "as-r3-first", "R3", "insufficient", "plan")
    _wait_for_next_second()
    _evidence_assessment(root, "as-r3-second", "R3", "failed", "execute")
    _evidence_assessment(root, "as-r2", "R2", "verified", "release")
    _create(
        root,
        "conductor:integration-report",
        "ev-full-report",
        {"phase": "ev-full", "effort": "alpha", "result": "fail", "revision": "abc"},
        "## Interfaces\n\nx\n\n## Assumptions\n\nx\n\n## Invariants\n\nx\n\n"
        "## Conflicts\n\nroute vs owner.\n",
    )
    for phase, state in (("ev-full", "ready"), ("ev-full", "merged"), ("ev-light", "ready")):
        _wait_for_next_second()
        _create(
            root,
            "conductor:release",
            f"{phase}-{state}",
            {"state": state, "phase": phase, "effort": "alpha"},
        )


def _check_view(check: dict[str, object] | None) -> dict[str, object] | None:
    if check is None:
        return None
    return {key: check[key] for key in ("method", "result", "evidence_kind", "signed_by")}


def _evidence_pin(root: Path, phase: str) -> dict[str, object]:
    client = TestClient(create_app(open_store(root)), raise_server_exceptions=False)
    response = client.get("/api/phase", params={"effort": "alpha", "phase": phase})
    assert response.status_code == 200, response.text
    detail = response.json()["detail"]
    evidence = detail["evidence"]
    if evidence is None:
        return {"structured": detail["structured"], "evidence": None}
    return {
        "structured": detail["structured"],
        "weight": evidence["weight"],
        "release_ready": evidence["release_ready"],
        "release_state": evidence["release_state"],
        "integration": evidence["integration"],
        "decisions": evidence["decisions"],
        "non_goals": evidence["non_goals"],
        "requirements": [
            {
                **{
                    key: row[key]
                    for key in (
                        "id",
                        "text",
                        "status",
                        "next",
                        "tasks",
                        "tasks_done",
                        "confidence",
                        "check_kind",
                    )
                },
                "latest_check": _check_view(row["latest_check"]),
                "has_check_at": row["check_at"] is not None,
            }
            for row in evidence["requirements"]
        ],
    }


def _requirement_pin(root: Path, phase: str, requirement: str) -> dict[str, object]:
    client = TestClient(create_app(open_store(root)), raise_server_exceptions=False)
    response = client.get(
        "/api/requirement", params={"effort": "alpha", "phase": phase, "id": requirement}
    )
    assert response.status_code == 200, response.text
    detail = response.json()["detail"]
    return {
        "text": detail["text"],
        "status": detail["status"],
        "next": detail["next"],
        "decisions": detail["decisions"],
        "tasks": [[row["subject"], row["status"]] for row in detail["tasks"]],
        "acceptances": [
            [row["subject"], _check_view(row["check"])] for row in detail["acceptances"]
        ],
        "assessments": [
            [row["status"], row["level"], row["next"], row["confidence"]]
            for row in detail["assessments"]
        ],
    }


PHASE_EVIDENCE_EXPECTED: dict[str, object] = json.loads(
    r"""{
 "full": {
  "decisions": [
   {
    "choice": "use owners",
    "subject": "d-one"
   },
   {
    "choice": "keep routes",
    "subject": "d-two"
   }
  ],
  "integration": {
   "conflicts": "route vs owner.",
   "result": "fail"
  },
  "non_goals": "keep display only.",
  "release_ready": false,
  "release_state": "merged",
  "requirements": [
   {
    "check_kind": "unit",
    "confidence": "",
    "has_check_at": true,
    "id": "R1",
    "latest_check": {
     "evidence_kind": "unit",
     "method": "check",
     "result": "pass",
     "signed_by": ""
    },
    "next": "",
    "status": "verified",
    "tasks": 2,
    "tasks_done": 1,
    "text": "first text."
   },
   {
    "check_kind": "",
    "confidence": "high",
    "has_check_at": true,
    "id": "R2",
    "latest_check": {
     "evidence_kind": "",
     "method": "check",
     "result": "pass",
     "signed_by": ""
    },
    "next": "",
    "status": "verified",
    "tasks": 1,
    "tasks_done": 1,
    "text": "second text."
   },
   {
    "check_kind": "",
    "confidence": "low",
    "has_check_at": true,
    "id": "R3",
    "latest_check": {
     "evidence_kind": "",
     "method": "check",
     "result": "pass",
     "signed_by": ""
    },
    "next": "execute",
    "status": "failed",
    "tasks": 0,
    "tasks_done": 0,
    "text": "third text."
   }
  ],
  "structured": true,
  "weight": "full"
 },
 "full-r1": {
  "acceptances": [
   [
    "a-r1",
    {
     "evidence_kind": "unit",
     "method": "check",
     "result": "pass",
     "signed_by": ""
    }
   ]
  ],
  "assessments": [],
  "decisions": [
   {
    "choice": "keep routes",
    "subject": "d-two"
   },
   {
    "choice": "use owners",
    "subject": "d-one"
   }
  ],
  "next": "",
  "status": "verified",
  "tasks": [
   [
    "t-b",
    "ready"
   ],
   [
    "t-a",
    "done"
   ]
  ],
  "text": "first text."
 },
 "full-r2": {
  "acceptances": [
   [
    "a-r2",
    {
     "evidence_kind": "",
     "method": "check",
     "result": "pass",
     "signed_by": ""
    }
   ]
  ],
  "assessments": [
   [
    "verified",
    "design",
    "release",
    "high"
   ]
  ],
  "decisions": [
   {
    "choice": "keep routes",
    "subject": "d-two"
   },
   {
    "choice": "use owners",
    "subject": "d-one"
   }
  ],
  "next": "",
  "status": "verified",
  "tasks": [
   [
    "t-a",
    "done"
   ]
  ],
  "text": "second text."
 },
 "full-r3": {
  "acceptances": [
   [
    "a-r2",
    {
     "evidence_kind": "",
     "method": "check",
     "result": "pass",
     "signed_by": ""
    }
   ]
  ],
  "assessments": [
   [
    "insufficient",
    "design",
    "plan",
    "high"
   ],
   [
    "failed",
    "design",
    "execute",
    "low"
   ]
  ],
  "decisions": [],
  "next": "execute",
  "status": "failed",
  "tasks": [],
  "text": "third text."
 },
 "light": {
  "decisions": [],
  "integration": null,
  "non_goals": "",
  "release_ready": true,
  "release_state": "ready",
  "requirements": [
   {
    "check_kind": "",
    "confidence": "",
    "has_check_at": false,
    "id": "R1",
    "latest_check": null,
    "next": "",
    "status": "verified",
    "tasks": 1,
    "tasks_done": 1,
    "text": "light one."
   },
   {
    "check_kind": "",
    "confidence": "",
    "has_check_at": false,
    "id": "R2",
    "latest_check": null,
    "next": "",
    "status": "unverified",
    "tasks": 0,
    "tasks_done": 0,
    "text": "light two."
   }
  ],
  "structured": false,
  "weight": "light"
 },
 "light-r1": {
  "acceptances": [
   [
    "a-light",
    {
     "evidence_kind": "",
     "method": "check",
     "result": "pass",
     "signed_by": ""
    }
   ]
  ],
  "assessments": [],
  "decisions": [],
  "next": "",
  "status": "verified",
  "tasks": [
   [
    "t-d",
    "done"
   ]
  ],
  "text": "light one."
 },
 "other": {
  "evidence": null,
  "structured": false
 },
 "other-r1": {
  "acceptances": [
   [
    "a-other",
    {
     "evidence_kind": "",
     "method": "check",
     "result": "fail",
     "signed_by": ""
    }
   ]
  ],
  "assessments": [],
  "decisions": [],
  "next": "",
  "status": "unverified",
  "tasks": [
   [
    "t-c",
    "ready"
   ]
  ],
  "text": ""
 }
}"""
)


def test_requirement_phase_evidence_route_pins() -> None:
    root = build_store()
    try:
        with pytest.MonkeyPatch.context() as patch:
            patch.setenv("ORCHESTRA_SIGNED_BY", "route-signer")
            _seed_phase_evidence(root)
            got = {
                "full": _evidence_pin(root, "ev-full"),
                "light": _evidence_pin(root, "ev-light"),
                "other": _evidence_pin(root, "ev-other"),
                "full-r1": _requirement_pin(root, "ev-full", "R1"),
                "full-r2": _requirement_pin(root, "ev-full", "R2"),
                "full-r3": _requirement_pin(root, "ev-full", "R3"),
                "light-r1": _requirement_pin(root, "ev-light", "R1"),
                "other-r1": _requirement_pin(root, "ev-other", "R1"),
            }
        assert got == PHASE_EVIDENCE_EXPECTED
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _seed_backlog_items(root: Path) -> None:
    _create(root, "score:effort", "alpha", {"goal": "ship alpha", "kind": "deliver"})
    _create(root, "score:effort", "beta", {"goal": "ship beta", "kind": "deliver"})
    _create(root, "composer:area", "billing", {"title": "Billing"}, "## Scope\n\nInvoices.")
    _create(root, "composer:placement", "alpha", {"area": "billing"})
    for subject, effort, status in (
        ("zeta-idea", "alpha", "open"),
        ("alpha-idea", "alpha", "open"),
        ("promoted-idea", "alpha", "promoted"),
        ("dismissed-idea", "alpha", "dismissed"),
        ("other-idea", "beta", "open"),
    ):
        _create(
            root,
            "composer:idea",
            subject,
            {"effort": effort, "status": status, "source": "chat", "phase": ""},
            f"Text of {subject}.\n",
        )


def test_snapshot_backlog_and_area_route_pins() -> None:
    root = build_store()
    try:
        with pytest.MonkeyPatch.context() as patch:
            patch.setenv("ORCHESTRA_SIGNED_BY", "route-signer")
            _seed_backlog_items(root)
            client = TestClient(create_app(open_store(root)), raise_server_exceptions=False)
            snapshot = client.get("/api/snapshot")
        assert snapshot.status_code == 200, snapshot.text
        effort = next(item for item in snapshot.json()["efforts"] if item["effort"] == "alpha")
        assert effort["area"] == "billing"
        assert [(item["subject"], item["text"], item["status"]) for item in effort["backlog"]] == [
            ("alpha-idea", "Text of alpha-idea.", "open"),
            ("zeta-idea", "Text of zeta-idea.", "open"),
        ]
    finally:
        shutil.rmtree(root, ignore_errors=True)
