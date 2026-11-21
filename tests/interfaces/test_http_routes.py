from __future__ import annotations

import json
import re
import shutil
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from conftest import build_store, run_cli
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from helpers import generic_body, schema_defs

from dashboard.backend.server.app import create_app
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
    r"""{
 "areas": {
  "body": [
   {
    "ideas": [
     {
      "area": "billing",
      "effort": "alpha",
      "phase": "p-one",
      "status": "open",
      "subject": "park-me",
      "text": "Park this idea."
     }
    ],
    "open_count": 1,
    "scope": "Invoices.",
    "subject": "billing",
    "title": "Billing"
   }
  ],
  "status": 200
 },
 "backlog": {
  "body": {
   "item": {
    "body": "Park this idea.\n",
    "effort": "alpha",
    "id": "<composer:idea:park-me>",
    "phase": "p-one",
    "record_type": "composer:idea",
    "source": "chat",
    "status": "open",
    "subject": "park-me",
    "text": "Park this idea."
   }
  },
  "status": 200
 },
 "error-backlog-unknown": {
  "body": {
   "error": "backlog item rec-missing not found"
  },
  "status": 404
 },
 "error-needs-unknown": {
  "body": {
   "error": "needs-you item rec-missing not found"
  },
  "status": 404
 },
 "error-phase-missing-param": {
  "body": {
   "detail": [
    {
     "input": null,
     "loc": [
      "query",
      "phase"
     ],
     "msg": "Field required",
     "type": "missing"
    }
   ]
  },
  "status": 422
 },
 "error-phase-unknown": {
  "body": {
   "error": "phase no-such-phase not found in alpha"
  },
  "status": 404
 },
 "error-record-unknown": {
  "body": {
   "error": "get --id rec-missing failed: unsafe record id 'rec-missing'"
  },
  "status": 404
 },
 "error-task-unknown": {
  "body": {
   "error": "get --type score:work-item failed: unsafe record id 'rec-missing'"
  },
  "status": 404
 },
 "hub": {
  "body": {
   "active_phases": [
    {
     "effort": "alpha",
     "href": "#/phase/alpha/p-one",
     "kind": "phase",
     "progress": {
      "blockers": {
       "more": 0,
       "shown": [
        "human gate: human-finding",
        "1 task not done"
       ],
       "text": "human gate: human-finding; 1 task not done"
      },
      "current": "spec",
      "reason": "human gate: human-finding",
      "repairs": null,
      "requirements": {
       "label": "1 of 1 proven",
       "proven": 1,
       "total": 1
      },
      "stages": [
       {
        "id": "spec",
        "state": "blocked"
       },
       {
        "id": "design",
        "state": "pending"
       },
       {
        "id": "tasks",
        "state": "pending"
       },
       {
        "id": "execute",
        "state": "pending"
       },
       {
        "id": "verify",
        "state": "pending"
       },
       {
        "id": "land",
        "state": "pending"
       },
       {
        "id": "close",
        "state": "pending"
       }
      ],
      "tasks": {
       "done": 0,
       "label": "0 of 1 done \u00b7 wave 1",
       "remaining": 1,
       "running": 0,
       "total": 1,
       "wave": 1
      },
      "weight": "full"
     },
     "reason": "Updated just now",
     "running": false,
     "step": "spec",
     "subject": "p-one",
     "title": "first phase",
     "updated_at": "<timestamp>"
    }
   ],
   "generated_at": "<timestamp>",
   "needs_you": [],
   "open_ideas": [
    {
     "effort": "alpha",
     "href": "#/backlog/alpha/<composer:idea:park-me>",
     "kind": "idea",
     "progress": null,
     "reason": "Idea \u00b7 parked just now",
     "running": false,
     "step": "",
     "subject": "<composer:idea:park-me>",
     "title": "Park this idea.",
     "updated_at": "<timestamp>"
    }
   ],
   "work_next": [
    {
     "effort": "alpha",
     "href": "#/backlog/alpha/<composer:idea:park-me>",
     "kind": "idea",
     "progress": null,
     "reason": "Idea \u00b7 parked just now",
     "running": false,
     "step": "",
     "subject": "<composer:idea:park-me>",
     "title": "Park this idea.",
     "updated_at": "<timestamp>"
    }
   ]
  },
  "status": 200
 },
 "journal": {
  "body": {
   "open": [
    {
     "assignee": "",
     "id": "<tuner:finding:human-finding>",
     "open": true,
     "phase": null,
     "record_type": "tuner:finding",
     "recorded_at": "<timestamp>",
     "subject": "human-finding",
     "task_id": "",
     "text": "a human must decide \u00b7 needs human",
     "write_root": ""
    },
    {
     "assignee": "",
     "id": "<score:continuity-question:alpha:port-choice>",
     "open": true,
     "phase": null,
     "record_type": "score:continuity-question",
     "recorded_at": "<timestamp>",
     "subject": "alpha",
     "task_id": "",
     "text": "port-choice \u00b7 open",
     "write_root": ""
    }
   ],
   "rest": []
  },
  "status": 200
 },
 "journal-unknown-effort": {
  "body": {
   "open": [],
   "rest": []
  },
  "status": 200
 },
 "needs": {
  "body": {
   "item": {
    "approval": {
     "confirm_choices": [
      {
       "action": "accept",
       "label": "Accept risk",
       "note_required": true
      }
     ]
    },
    "body": "## Evidence\n\nplaceholder text for Evidence.\n\n## Consequence\n\nplaceholder text for Consequence.\n\n## Follow-up\n\nplaceholder text for Follow-up.\n",
    "id": "<tuner:finding:human-finding>",
    "kind": "needs-human",
    "next": "",
    "phase": "",
    "record_type": "tuner:finding",
    "requirement": "",
    "result": "",
    "revision": "<rev:tuner:finding:human-finding>",
    "status": "",
    "subject": "human-finding",
    "task_id": "",
    "text": "a human must decide"
   }
  },
  "status": 200
 },
 "phase": {
  "body": {
   "decisions": {
    "groups": []
   },
   "detail": {
    "awaiting_signoff": true,
    "body": "## Problem\n\nplaceholder text for Problem.\n\n## Approach\n\nplaceholder text for Approach.\n\n## Exit criteria\n\nplaceholder text for Exit criteria.\n",
    "constraints": [],
    "decisions": [],
    "design_body": "",
    "effort": "alpha",
    "evidence": {
     "decisions": [],
     "integration": null,
     "non_goals": "placeholder text.",
     "phase": "p-one",
     "release_ready": true,
     "release_state": "",
     "requirements": [
      {
       "check_at": null,
       "check_kind": "",
       "confidence": "",
       "id": "R1",
       "latest_check": null,
       "next": "",
       "phase": "p-one",
       "status": "verified",
       "tasks": 1,
       "tasks_done": 0,
       "text": ""
      }
     ],
     "stage": "spec",
     "stage_reason": "human gate: human-finding",
     "weight": "full"
    },
    "milestone": "",
    "milestone_title": "",
    "proof": null,
    "spec_body": "## Requirements\n\n- R1: the route keeps its body.\n\n## Acceptance criteria\n\nplaceholder text.\n\n## Constraints\n\nplaceholder text.\n\n## Non-goals\n\nplaceholder text.\n\n## Invariants\n\nplaceholder text.\n\n## Assumptions\n\nplaceholder text.\n",
    "state": "in_progress",
    "structured": true,
    "subject": "p-one",
    "tasks": [
     {
      "assignee": "",
      "attempts": 0,
      "depends_on": [],
      "estimate_minutes": null,
      "executor": "subagent",
      "id": "<score:work-item:t-one>",
      "last_record_at": null,
      "phase": "p-one",
      "retry_budget": 2,
      "running_since": null,
      "size": "",
      "status": "ready",
      "subject": "t-one",
      "title": "first task",
      "waits_on": [],
      "wave": 1,
      "write_root": ""
     }
    ],
    "title": "first phase"
   },
   "tabs": [
    "overview",
    "spec",
    "design",
    "decisions",
    "evidence",
    "tasks"
   ]
  },
  "status": 200
 },
 "record": {
  "body": {
   "record": {
    "body": "## Evidence\n\nplaceholder text for Evidence.\n\n## Consequence\n\nplaceholder text for Consequence.\n\n## Follow-up\n\nplaceholder text for Follow-up.\n",
    "derived": {
     "write_order": 8
    },
    "id": "<tuner:finding:human-finding>",
    "lifecycle_state": "asserted",
    "payload": {
     "basis": "observed",
     "claim": "a human must decide",
     "effort": "alpha",
     "invalidated_when": "decision recorded",
     "needs": "human"
    },
    "record_type": "tuner:finding",
    "recorded_at": "<timestamp>",
    "relationships": {},
    "revision": "<rev:tuner:finding:human-finding>",
    "subject": "human-finding"
   }
  },
  "status": 200
 },
 "requirement": {
  "body": {
   "detail": {
    "acceptances": [
     {
      "check": {
       "evidence_kind": "",
       "id": "<tuner:check-run:unsigned-check>",
       "method": "manual",
       "recorded_at": "<timestamp>",
       "result": "pass",
       "revision": "abc",
       "signed_by": ""
      },
      "criterion": "the route keeps its body",
      "id": "<score:acceptance:t-one-acc>",
      "method": "check",
      "subject": "t-one-acc",
      "verify_command": "uv run pytest -q"
     }
    ],
    "assessments": [],
    "decisions": [],
    "id": "R1",
    "next": "",
    "phase": "p-one",
    "status": "verified",
    "tasks": [
     {
      "assignee": "",
      "attempts": 0,
      "depends_on": [],
      "estimate_minutes": null,
      "executor": "subagent",
      "id": "<score:work-item:t-one>",
      "last_record_at": null,
      "phase": "p-one",
      "retry_budget": 2,
      "running_since": null,
      "size": "",
      "status": "ready",
      "subject": "t-one",
      "title": "first task",
      "waits_on": [],
      "wave": 1,
      "write_root": ""
     }
    ],
    "text": ""
   }
  },
  "status": 200
 },
 "requirement-unknown-phase": {
  "body": {
   "detail": {
    "acceptances": [],
    "assessments": [],
    "decisions": [],
    "id": "R1",
    "next": "",
    "phase": "no-such-phase",
    "status": "unverified",
    "tasks": [],
    "text": ""
   }
  },
  "status": 200
 },
 "snapshot": {
  "body": {
   "efforts": [
    {
     "area": "",
     "backlog": [
      {
       "id": "<composer:idea:park-me>",
       "phase": "p-one",
       "source": "chat",
       "status": "open",
       "subject": "park-me",
       "text": "Park this idea."
      }
     ],
     "dormant": false,
     "effort": "alpha",
     "finished": false,
     "goal": "ship alpha",
     "kind": "deliver",
     "milestones": [],
     "needs_you": [
      {
       "id": "<tuner:finding:human-finding>",
       "kind": "needs-human",
       "next": "",
       "phase": "",
       "record_type": "tuner:finding",
       "requirement": "",
       "result": "",
       "revision": "<rev:tuner:finding:human-finding>",
       "status": "",
       "subject": "human-finding",
       "task_id": "",
       "text": "a human must decide"
      },
      {
       "id": "<tuner:check-run:unsigned-check>",
       "kind": "unsigned-check",
       "next": "",
       "phase": "",
       "record_type": "tuner:check-run",
       "requirement": "",
       "result": "",
       "revision": "<rev:tuner:check-run:unsigned-check>",
       "status": "",
       "subject": "t-one-acc",
       "task_id": "<score:work-item:t-one>",
       "text": "the route keeps its body pass"
      },
      {
       "id": "<score:continuity-question:alpha:port-choice>",
       "kind": "open-question",
       "next": "",
       "phase": "",
       "record_type": "score:continuity-question",
       "requirement": "",
       "result": "",
       "revision": "<rev:score:continuity-question:alpha:port-choice>",
       "status": "",
       "subject": "alpha",
       "task_id": "",
       "text": "port-choice"
      }
     ],
     "phases": [
      {
       "awaiting_signoff": true,
       "done": 0,
       "elapsed_minutes": null,
       "id": "<score:phase:p-one>",
       "in_progress": [],
       "milestone": "",
       "milestone_title": "",
       "ordinal": 1,
       "release_ready": true,
       "requirements": 1,
       "sitting": "",
       "stage": "spec",
       "state": "in_progress",
       "subject": "p-one",
       "suite": "",
       "title": "first phase",
       "total": 1,
       "unset_estimates": 1,
       "verified": 1
      }
     ],
     "position": "",
     "release_ready": true,
     "tasks": [
      {
       "assignee": "",
       "attempts": 0,
       "depends_on": [],
       "estimate_minutes": null,
       "executor": "subagent",
       "id": "<score:work-item:t-one>",
       "last_record_at": null,
       "phase": "p-one",
       "retry_budget": 2,
       "running_since": null,
       "size": "",
       "status": "ready",
       "subject": "t-one",
       "title": "first task",
       "waits_on": [],
       "wave": 1,
       "write_root": ""
      }
     ]
    }
   ],
   "generated_at": "<timestamp>",
   "store": "<store>/.canon",
   "token": "<token>"
  },
  "status": 200
 },
 "task": {
  "body": {
   "detail": {
    "acceptances": [
     {
      "check": null,
      "criterion": "the route keeps its body",
      "id": "<score:acceptance:t-one-acc>",
      "method": "check",
      "subject": "t-one-acc",
      "verify_command": "uv run pytest -q"
     }
    ],
    "agent_work": [],
    "assignee": "",
    "blocks": [],
    "body": "## Description\n\nplaceholder text for Description.\n",
    "decisions": [],
    "depends_on": [],
    "effort": "alpha",
    "estimate_minutes": null,
    "executor": "subagent",
    "id": "<score:work-item:t-one>",
    "phase": "p-one",
    "related": [],
    "requirements": [
     "R1"
    ],
    "running_since": null,
    "size": "",
    "status": "ready",
    "subject": "t-one",
    "timeline": [],
    "title": "first task",
    "wave": 1,
    "write_root": ""
   }
  },
  "status": 200
 },
 "token": {
  "body": {
   "token": "<token>"
  },
  "status": 200
 }
}"""
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
