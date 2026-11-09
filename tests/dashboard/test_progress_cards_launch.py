from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from subprocess import CompletedProcess

import pytest
import test_web_dashboard_launch as launch
from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))

Cli = Callable[..., CompletedProcess[str]]

EFFORT = "alpha"
PHASE = "cards-phase"
REQUIREMENTS = ("R1", "R2", "R3")
SECTIONS = (
    "Requirements",
    "Acceptance criteria",
    "Constraints",
    "Non-goals",
    "Invariants",
    "Assumptions",
)


def _create(
    cli: Cli, record_type: str, subject: str, payload: dict[str, object], body: str = ""
) -> dict:
    args = [
        "create",
        "--type",
        record_type,
        "--subject",
        subject,
        "--payload",
        json.dumps(payload),
        "--body",
        body or f"text of {subject}\n",
    ]
    result = cli(*args)
    assert result.returncode == 0, f"create {record_type} {subject}: {result.stdout}{result.stderr}"
    return json.loads(result.stdout)["record"]


def _transition(cli: Cli, record_type: str, subject: str, *states: str) -> None:
    for state in states:
        result = cli("update", "--type", record_type, "--subject", subject, "--transition", state)
        assert result.returncode == 0, f"update {subject}: {result.stdout}{result.stderr}"


def _seed(cli: Cli) -> None:
    _create(cli, "score:effort", EFFORT, {"goal": "ship alpha", "kind": "deliver"})
    sections = "\n\n".join(
        f"## {name}\n\nText." for name in ("Problem", "Approach", "Exit criteria")
    )
    _create(
        cli,
        "score:phase",
        PHASE,
        {"title": "Cards phase", "ordinal": 1, "effort": EFFORT},
        sections,
    )
    _transition(cli, "score:phase", PHASE, "in_progress")
    lines = "\n".join(f"{rid}: text of {rid}" for rid in REQUIREMENTS)
    body = "\n\n".join(
        f"## {name}\n\n{lines if name == 'Requirements' else 'none'}" for name in SECTIONS
    )
    _create(
        cli,
        "score:specification",
        PHASE,
        {
            "phase": PHASE,
            "effort": EFFORT,
            "requirements": list(REQUIREMENTS),
            "weight": "light",
        },
        body,
    )
    for index in range(1, 5):
        subject = f"task-{index}"
        _create(
            cli,
            "score:work-item",
            subject,
            {
                "title": subject,
                "phase": PHASE,
                "kind": "deliver",
                "assignee": "",
                "effort": EFFORT,
                "attempts": 0,
                "estimate_minutes": 0,
            },
            "## Description\n\nText.",
        )
        if index <= 2:
            _transition(cli, "score:work-item", subject, "in_progress", "done")
    for requirement in REQUIREMENTS:
        acceptance = _create(
            cli,
            "score:acceptance",
            f"acc-{requirement}",
            {
                "criterion": requirement,
                "method": "check",
                "phase": PHASE,
                "effort": EFFORT,
                "verify_command": "true",
                "requirement": requirement,
            },
        )
        if requirement != "R3":
            _create(
                cli,
                "tuner:check-run",
                f"run-{requirement}",
                {
                    "criterion_id": acceptance["id"],
                    "revision": "dirty",
                    "result": "pass",
                    "effort": EFFORT,
                    "method": "check",
                    "signed_by": "ayin",
                    "requirement": requirement,
                    "evidence_kind": "unit",
                },
            )


def test_r17_card_figures_equal_phase_page_values(
    store: Path, cli: Cli, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed(cli)
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    port = launch._free_port()
    proc = launch._spawn(
        store, ["--port", str(port)], launch._env(home), tmp_path / "out", tmp_path / "err"
    )
    try:
        status, _type, body = launch._get(port, "/api/hub")
        assert status == 200, body
        hub = json.loads(body)
        status, _type, body = launch._get(port, f"/api/phase?effort={EFFORT}&phase={PHASE}")
        assert status == 200, body
        detail = json.loads(body)["detail"]
    finally:
        launch._stop(proc)

    cards = [card for card in hub["active_phases"] if card["subject"] == PHASE]
    assert len(cards) == 1
    progress = cards[0]["progress"]
    tasks = detail["tasks"]
    statuses = [row["status"] for row in detail["evidence"]["requirements"]]

    assert progress["tasks"]["total"] == len(tasks) == 4
    assert progress["tasks"]["done"] == sum(1 for row in tasks if row["status"] == "done") == 2
    assert progress["requirements"]["total"] == len(statuses) == 3
    assert progress["requirements"]["proven"] == statuses.count("verified") == 2
