"""The workflow, the handoff views and the dashboard report one stage and one reason per phase."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest
from canon_support import create
from conductor_support import EFFORT, HEAD, PHASE, Cli, Phase, ready_for_verify
from conductor_support import seed as seed_phase
from conftest import git
from fastapi.testclient import TestClient

from dashboard.backend.server.app import create_app
from orchestra import cli as orchestra_cli
from orchestra.canon.project import open_store
from orchestra.conductor.workflow import step_stage

OTHER_HEAD = "b" * 40
GITHUB_PR = "github-pr"
GATE_PREFIX = "human gate: "
WORKFLOW_GATE_PREFIX = "human decision blocks this phase: "
HANDOFF_LINE = re.compile(
    rf"^- \*\*{PHASE}\*\*: .*?stage: (?P<stage>\w+)(?: \((?P<reason>.*)\))? _\(id: ", re.MULTILINE
)


@dataclass(frozen=True)
class Seen:
    stage: str | None
    reason: str


@dataclass(frozen=True)
class Case:
    build: Callable[[Phase], None]
    landing: tuple[str, ...]
    expected: Seen
    adapter: str = ""


def _proof(phase: Phase) -> None:
    phase.create(
        "conductor:proof-packet",
        PHASE,
        {"phase": PHASE, "effort": EFFORT, "revision": HEAD, "base": "main", "kind": "claims"},
        "## Look\nl\n\n## Machine\nm\n\n## Attention\nnone\n\n## Diff\nno tree change\n",
    )


def _landing(phase: Phase, result: str, head: str = HEAD) -> None:
    phase.create(
        "conductor:landing",
        PHASE,
        {
            "phase": PHASE,
            "effort": EFFORT,
            "number": 7,
            "url": "https://github.com/o/r/pull/7",
            "head_sha": head,
            "result": result,
        },
    )


def _use_adapter(phase: Phase, adapter: str) -> None:
    path = phase.store / "orchestra.toml"
    path.write_text(path.read_text() + f'\n[land]\nadapter = "{adapter}"\n', encoding="utf-8")


def _blocked(phase: Phase) -> None:
    create(
        open_store(phase.store),
        "score:continuity-question",
        EFFORT,
        {"scope": EFFORT, "owner": "human", "blocking": True},
    )


def _stale_proof(phase: Phase) -> None:
    _proof(phase)
    _landing(phase, "success", OTHER_HEAD)


def _failed_landing(phase: Phase) -> None:
    _proof(phase)
    _landing(phase, "fail")


def _landed(phase: Phase) -> None:
    _proof(phase)
    _landing(phase, "success")


def _merged(phase: Phase) -> None:
    _landed(phase)
    git(phase.repo, "merge", "-q", "phase/x")


CASES: dict[str, Case] = {
    "blocked": Case(_blocked, (), Seen("verify", f"{GATE_PREFIX}{EFFORT}")),
    "stale-proof": Case(_stale_proof, (), Seen("land", "stale-proof")),
    "failed-landing": Case(_failed_landing, (), Seen("land", "failed-landing")),
    "failed-landing-github-pr": Case(
        _failed_landing, (), Seen("land", "failed-landing"), adapter=GITHUB_PR
    ),
    "landed-unmerged": Case(_landed, ("Branch: phase/x",), Seen("close", "awaiting-merge")),
    "merged": Case(_merged, ("Branch: phase/x",), Seen("close", "ready-to-close")),
    "missing-branch": Case(_landed, (), Seen("close", "ready-to-close")),
    "git-read-failure": Case(
        _landed, ("Branch: phase/x", "Base: no-such-base"), Seen("close", "git-read-failed")
    ),
    "closed": Case(_merged, ("Branch: phase/x",), Seen(None, "")),
}


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    capsys.readouterr()
    assert orchestra_cli.main(list(argv)) == 0
    return capsys.readouterr().out


def _handoff(capsys: pytest.CaptureFixture[str]) -> Seen:
    found = HANDOFF_LINE.search(_run(capsys, "handoff", "--all"))
    if found is None:
        return Seen(None, "")
    return Seen(found["stage"], found["reason"] or "")


def _hub(client: TestClient) -> Seen:
    cards = [
        card for card in client.get("/api/hub").json()["active_phases"] if card["subject"] == PHASE
    ]
    if not cards:
        return Seen(None, "")
    [card] = cards
    progress = card["progress"]
    assert card["step"] == progress["current"]
    return Seen(progress["current"] or None, progress["reason"])


def _phase_page(client: TestClient) -> Seen:
    response = client.get("/api/phase", params={"effort": EFFORT, "phase": PHASE})
    assert response.status_code == 200, response.text
    evidence = response.json()["detail"]["evidence"]
    return Seen(evidence["stage"] or None, evidence["stage_reason"])


def _workflow(store: Path, capsys: pytest.CaptureFixture[str]) -> Seen:
    """Read the workflow through `workflow next`.

    The workflow offers the first step whose stage is not done, so that step is the current stage.
    After `land` it offers nothing, and `step_stage` tells a phase waiting to close from a closed
    one. It names the reason of a blocked step in its own words, and for the land and close stages
    it names the brief stage (land, repair-ci or close) instead of the assessment reason.
    """
    where = ["--store", str(store)]
    preview = json.loads(_run(capsys, "workflow", "preview", EFFORT, PHASE, "phase", "--json"))
    started = json.loads(
        _run(
            capsys,
            "workflow",
            "start",
            EFFORT,
            PHASE,
            "phase",
            "--snapshot-token",
            preview["snapshot_token"],
            "--json",
            *where,
        )
    )
    shown = json.loads(
        _run(capsys, "workflow", "next", started["run"]["subject"], "--no-brief", "--json", *where)
    )
    project = open_store(store)
    records = project.records()
    if not shown["actions"]:
        stage = step_stage(project, records, PHASE, "land")
        return Seen(stage, stage or "")
    [action] = shown["actions"]
    if action["state"] == "blocked":
        return Seen(action["step"], action["reason"])
    return Seen(action["step"], step_stage(project, records, PHASE, action["step"]) or "")


def _as_workflow_reason(case: Case) -> str:
    stage, reason = case.expected.stage, case.expected.reason
    if reason.startswith(GATE_PREFIX):
        return WORKFLOW_GATE_PREFIX + reason.removeprefix(GATE_PREFIX)
    if stage == "land":
        return "repair-ci" if reason == "failed-landing" and case.adapter == GITHUB_PR else "land"
    if stage == "close":
        return "close"
    return reason


def _build(store: Path, cli: Cli, name: str, monkeypatch: pytest.MonkeyPatch) -> tuple[Case, Phase]:
    case = CASES[name]
    phase = seed_phase(store, cli, landing_lines=case.landing)
    ready_for_verify(phase)
    if case.adapter:
        _use_adapter(phase, case.adapter)
    case.build(phase)
    project = open_store(store)
    record = project.resolve("score:phase", PHASE)
    for transition in ("in_progress", *(("done",) if name == "closed" else ())):
        record = project.update(record["id"], record_type="score:phase", transition=transition)
    monkeypatch.chdir(store)
    return case, phase


@pytest.mark.parametrize("name", CASES)
def test_workflow_handoff_and_dashboard_report_the_same_stage(
    name: str,
    store: Path,
    cli: Cli,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case, _ = _build(store, cli, name, monkeypatch)
    client = TestClient(create_app(open_store(store)))

    seen = {
        "handoff": _handoff(capsys).stage,
        "hub": _hub(client).stage,
        "phase page": _phase_page(client).stage,
        "workflow": _workflow(store, capsys).stage,
    }

    assert seen == dict.fromkeys(seen, case.expected.stage)


@pytest.mark.parametrize("name", CASES)
def test_workflow_handoff_and_dashboard_report_the_same_reason(
    name: str,
    store: Path,
    cli: Cli,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case, _ = _build(store, cli, name, monkeypatch)
    client = TestClient(create_app(open_store(store)))

    assert _handoff(capsys).reason == case.expected.reason
    assert _hub(client).reason == case.expected.reason
    assert _phase_page(client).reason == case.expected.reason
    assert _workflow(store, capsys).reason == _as_workflow_reason(case)
