from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from canon_support import REPO, create, make_project
from fastapi.testclient import TestClient

from dashboard.backend.server.app import create_app
from orchestra.canon import project as project_mod
from orchestra.canon import record as record_mod
from orchestra.canon.project import Project, open_store
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor import gate, phase_progress, wave
from orchestra.conductor.verification.requirements import (
    RequirementState,
    release_ready,
    requirement_status,
)

EFFORT = "ef"
MIX = "mix"
TASK = "a"
PHASE_BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n"
MIX_BODY = (
    f"{PHASE_BODY}\n## Landing\n\nbranch: phase/{MIX}\n"
    f"worktree: <repo>/.worktrees/{MIX}\nbase: main\n"
)
EVIDENCE = {
    "subject": TASK,
    "kind": "deliver",
    "result": "pass",
    "verdict": "pass",
    "evidence": "ran the acceptance",
}


@dataclass(frozen=True)
class Scenario:
    name: str
    expected: RequirementState
    acceptances: int = 1
    method: str = "check"


SCENARIOS = (
    Scenario("passing", "verified"),
    Scenario("failing", "failed"),
    Scenario("corrected-to-pass", "verified"),
    Scenario("corrected-to-fail", "failed"),
    Scenario("stale-pass-then-fail", "failed"),
    Scenario("stale-fail-then-pass", "verified"),
    Scenario("equal-time-fail-written-last", "failed"),
    Scenario("equal-time-pass-written-last", "verified"),
    Scenario("manual-signed", "verified", method="manual"),
    Scenario("manual-unsigned", "unverified", method="manual"),
    Scenario("missing-run", "unverified"),
    Scenario("no-acceptance", "unverified", acceptances=0),
    Scenario("pass-and-missing", "unverified", acceptances=2),
    Scenario("pass-and-fail", "failed", acceptances=2),
)
LANDED = "landed-pass"
GATE_SCENARIOS = tuple(s for s in SCENARIOS if s.acceptances)


class Clock:
    def __init__(self) -> None:
        self.tick = 0
        self.frozen: str | None = None

    def next(self) -> str:
        if self.frozen is not None:
            return self.frozen
        self.tick += 1
        stamp = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=self.tick)
        return stamp.isoformat()


@dataclass(frozen=True)
class World:
    project: Project
    root: Path
    mix: dict[str, str]
    landing: JsonObject


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _orchestra(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(REPO))
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


def _spec_body(requirements: list[str]) -> str:
    lines = "\n".join(f"{requirement}: Behavior {requirement}." for requirement in requirements)
    return (
        f"## Requirements\n\n{lines}\n\n## Acceptance criteria\n\nx\n\n## Constraints\n\nx\n\n"
        "## Non-goals\n\nx\n\n## Invariants\n\nx\n\n## Assumptions\n\nx"
    )


def _phase(
    project: Project, phase: str, ordinal: int, requirements: list[str], body: str = PHASE_BODY
) -> None:
    record = create(
        project, "score:phase", phase, {"title": phase, "ordinal": ordinal, "effort": EFFORT}, body
    )
    create(
        project,
        "score:specification",
        phase,
        {"weight": "full", "phase": phase, "effort": EFFORT, "requirements": requirements},
        _spec_body(requirements),
    )
    project.update(record["id"], record_type="score:phase", transition="in_progress")


def _acceptance(
    project: Project, phase: str, subject: str, requirement: str, method: str
) -> Record:
    return create(
        project,
        "score:acceptance",
        subject,
        {
            "method": method,
            "phase": phase,
            "effort": EFFORT,
            "verify_command": "true",
            "requirement": requirement,
        },
    )


def _run(
    project: Project,
    acceptance: Record,
    result: str,
    revision: str,
    *,
    signed_by: str = "",
) -> Record:
    return create(
        project,
        "tuner:check-run",
        acceptance["subject"],
        {
            "criterion_id": acceptance["id"],
            "result": result,
            "revision": revision,
            "effort": EFFORT,
            "method": acceptance["payload"]["method"],
            "signed_by": signed_by,
        },
    )


def _correct(project: Project, run: Record, result: str) -> None:
    project.correct(run["id"], payload={"result": result})


def _seed(
    project: Project,
    clock: Clock,
    phase: str,
    requirement: str,
    scenario: Scenario,
    revision: str,
) -> None:
    acceptances = [
        _acceptance(
            project, phase, f"{phase}-{requirement}-{n}".lower(), requirement, scenario.method
        )
        for n in range(scenario.acceptances)
    ]
    if not acceptances:
        return
    first = acceptances[0]

    def run(result: str, *, signed_by: str = "") -> Record:
        return _run(project, first, result, revision, signed_by=signed_by)

    match scenario.name:
        case "passing" | "pass-and-missing":
            run("pass")
        case "failing":
            run("fail")
        case "corrected-to-pass":
            _correct(project, run("fail"), "pass")
        case "corrected-to-fail":
            _correct(project, run("pass"), "fail")
        case "stale-pass-then-fail":
            run("pass")
            run("fail")
        case "stale-fail-then-pass":
            run("fail")
            run("pass")
        case "equal-time-fail-written-last" | "equal-time-pass-written-last":
            first_result, last_result = (
                ("pass", "fail") if "fail-written-last" in scenario.name else ("fail", "pass")
            )
            clock.frozen = clock.next()
            run(first_result)
            run(last_result)
            clock.frozen = None
        case "manual-signed":
            run("pass", signed_by="alice")
        case "manual-unsigned":
            run("pass")
        case "pass-and-fail":
            run("pass")
            _run(project, acceptances[1], "fail", revision)
        case _:
            pass


def _requirement_ids(count: int) -> list[str]:
    return [f"R{n}" for n in range(1, count + 1)]


@pytest.fixture(scope="module")
def world(tmp_path_factory: pytest.TempPathFactory) -> Iterator[World]:
    root = tmp_path_factory.mktemp("agreement")
    clock = Clock()
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(record_mod, "now", clock.next)
        patch.setattr(project_mod, "now", clock.next)
        project = make_project(root)
        _git(root, "config", "user.email", "t@example.com")
        _git(root, "config", "user.name", "t")
        (root / "base.txt").write_text("base\n")
        _git(root, "add", "base.txt")
        _git(root, "commit", "-qm", "base")
        _git(root, "branch", "-M", "main")
        create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
        mix_scenarios = (Scenario(LANDED, "verified"), *SCENARIOS)
        requirements = _requirement_ids(len(mix_scenarios))
        _phase(project, MIX, 1, requirements, MIX_BODY)
        _git(root, "branch", f"phase/{MIX}", "main")
        (root / ".worktrees").mkdir()
        _git(root, "worktree", "add", "-q", str(root / ".worktrees" / MIX), f"phase/{MIX}")
        create(
            project,
            "score:work-item",
            TASK,
            {
                "title": TASK,
                "phase": MIX,
                "kind": "deliver",
                "assignee": "",
                "effort": EFFORT,
                "executor": "inline",
                "requirements": requirements,
            },
            "## Description\n\nR1: Behavior R1.\n\n## Approach\n\nDo it.",
        )
        _acceptance(project, MIX, TASK, "R1", "check")
        wave.start(project, root, MIX)
        revision = _git(root / ".worktrees" / MIX, "rev-parse", "HEAD")
        mix: dict[str, str] = {LANDED: "R1"}
        for requirement, scenario in zip(requirements[1:], SCENARIOS, strict=True):
            mix[scenario.name] = requirement
            _seed(project, clock, MIX, requirement, scenario, revision)
        for ordinal, scenario in enumerate(SCENARIOS, start=2):
            phase = f"s-{scenario.name}"
            _phase(project, phase, ordinal, ["R1"])
            _seed(project, clock, phase, "R1", scenario, revision)
        evidence = root / "evidence.json"
        evidence.write_text(json.dumps(EVIDENCE))
        landed = _orchestra(root, "task", "land", TASK, "--evidence", str(evidence), "--json")
        assert landed.returncode in (0, 1), landed.stderr
        landing: JsonObject = json.loads(landed.stdout)
        yield World(open_store(root), root, mix, landing)


Statuses = dict[tuple[str, str], str]


def _expected_statuses(world: World) -> Statuses:
    expected: Statuses = {(MIX, world.mix[LANDED]): "verified"}
    for scenario in SCENARIOS:
        expected[(MIX, world.mix[scenario.name])] = scenario.expected
        expected[(f"s-{scenario.name}", "R1")] = scenario.expected
    return expected


def _phases(world: World) -> list[str]:
    return [MIX, *(f"s-{scenario.name}" for scenario in SCENARIOS)]


def _shared_operation(world: World) -> Statuses:
    records = world.project.records()
    return {
        (phase, requirement): status.status
        for phase in _phases(world)
        for requirement, status in requirement_status(records, phase).items()
    }


def _view(world: World, *args: str) -> Statuses:
    result = _orchestra(world.root, "view", *args, "--effort", EFFORT)
    assert result.returncode == 0, result.stderr
    statuses: Statuses = {}
    phase = ""
    for line in result.stdout.splitlines():
        heading = re.match(r"## (?:Phase )?(\S+)$", line)
        if heading:
            phase = heading.group(1)
        found = re.match(r"- \*\*(R\d+)\*\*: (\S+)", line)
        if found:
            statuses[(phase, found.group(1))] = found.group(2)
    return statuses


@pytest.fixture(scope="module")
def client(world: World) -> TestClient:
    return TestClient(create_app(open_store(world.root)), raise_server_exceptions=False)


def _dashboard_phase_route(client: TestClient, world: World) -> Statuses:
    statuses: Statuses = {}
    for phase in _phases(world):
        response = client.get("/api/phase", params={"effort": EFFORT, "phase": phase})
        assert response.status_code == 200, response.text
        for row in response.json()["detail"]["evidence"]["requirements"]:
            statuses[(phase, row["id"])] = row["status"]
    return statuses


def _dashboard_requirement_route(client: TestClient, expected: Statuses) -> Statuses:
    statuses: Statuses = {}
    for phase, requirement in expected:
        response = client.get(
            "/api/requirement", params={"effort": EFFORT, "phase": phase, "id": requirement}
        )
        assert response.status_code == 200, response.text
        statuses[(phase, requirement)] = response.json()["detail"]["status"]
    return statuses


def _closure_not_verified(world: World) -> set[str]:
    reasons = world.landing["reasons"]
    assert isinstance(reasons, list)
    prefix = "requirements not verified: "
    listed = [reason for reason in reasons if isinstance(reason, str) and prefix in reason]
    assert len(listed) == 1, reasons
    return set(listed[0].removeprefix(prefix).split(", "))


def _readiness(world: World, phase: str) -> tuple[bool, str]:
    records = world.project.records()
    readiness = phase_progress.verification_readiness(
        phase_progress.acceptance_holds(records, phase), "not-required"
    )
    return readiness.ready, readiness.reason


def _gate_holds(world: World, phase: str) -> bool:
    terms = gate.gate_terms(open_store(world.root), phase)
    return all(
        term.holds
        for term in terms
        if term.name.startswith(("acceptance-passes:", "manual-check-signed:"))
    )


def test_r1_agreement_shared_operation_reports_every_scenario(world: World) -> None:
    assert _shared_operation(world) == _expected_statuses(world)


def _shown_phases(shown: Statuses) -> set[str]:
    return {phase for phase, _ in shown}


def _assert_view_agrees(world: World, shown: Statuses, phases: set[str]) -> None:
    expected = _expected_statuses(world)
    assert _shown_phases(shown) == phases
    assert shown == {key: value for key, value in expected.items() if key[0] in phases}


def test_r1_agreement_status_view_matches_shared_operation(world: World) -> None:
    _assert_view_agrees(world, _view(world, "status"), {MIX})


def test_r1_agreement_plan_view_matches_shared_operation(world: World) -> None:
    _assert_view_agrees(world, _view(world, "plan"), set(_phases(world)))


def test_r1_agreement_verification_view_matches_shared_operation(world: World) -> None:
    phases = set(_phases(world)) - {"s-no-acceptance"}
    _assert_view_agrees(world, _view(world, "verification"), phases)


def test_r1_agreement_dashboard_phase_route_matches_shared_operation(
    world: World, client: TestClient
) -> None:
    assert _dashboard_phase_route(client, world) == _expected_statuses(world)


def test_r1_agreement_dashboard_requirement_route_matches_shared_operation(
    world: World, client: TestClient
) -> None:
    expected = _expected_statuses(world)
    assert _dashboard_requirement_route(client, expected) == expected


def test_r1_agreement_task_close_leaves_exactly_the_unverified_requirements(world: World) -> None:
    expected = _expected_statuses(world)
    unverified = {
        requirement
        for (phase, requirement), status in expected.items()
        if phase == MIX and status != "verified"
    }
    assert world.landing["state"] == "in_progress"
    assert _closure_not_verified(world) == unverified


def test_r1_agreement_workflow_readiness_names_the_first_unverified_requirement(
    world: World,
) -> None:
    expected = _expected_statuses(world)
    first = next(
        (requirement, status)
        for (phase, requirement), status in expected.items()
        if phase == MIX and status != "verified"
    )
    assert _readiness(world, MIX) == (False, f"requirement {first[0]} is {first[1]}")


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda scenario: scenario.name)
def test_r1_agreement_workflow_readiness_matches_each_scenario(
    world: World, scenario: Scenario
) -> None:
    phase = f"s-{scenario.name}"
    records = world.project.records()
    ready, reason = _readiness(world, phase)
    record = [r for r in records if r["record_type"] == "score:phase" and r["subject"] == phase][-1]
    model = phase_progress.read_phase(record)
    stage = phase_progress.verify_step(world.project, records, model)
    if scenario.expected == "verified":
        assert (ready, reason) == (True, "")
        assert stage != "analyze"
    else:
        assert (ready, reason) == (False, f"requirement R1 is {scenario.expected}")
        assert stage == "analyze"


@pytest.mark.parametrize("scenario", GATE_SCENARIOS, ids=lambda scenario: scenario.name)
def test_r1_agreement_phase_gate_matches_each_scenario(world: World, scenario: Scenario) -> None:
    assert _gate_holds(world, f"s-{scenario.name}") == (scenario.expected == "verified")


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda scenario: scenario.name)
def test_r1_agreement_release_readiness_matches_each_scenario(
    world: World, scenario: Scenario
) -> None:
    ready = release_ready(world.project.records(), f"s-{scenario.name}")
    assert ready == (scenario.expected == "verified")


def test_r1_agreement_release_readiness_is_false_while_any_requirement_is_not_verified(
    world: World,
) -> None:
    assert not release_ready(world.project.records(), MIX)


def test_r1_agreement_handoff_lists_unsigned_manual_checks_for_unverified_manual_scenarios(
    world: World,
) -> None:
    result = _orchestra(world.root, "handoff", "--effort", EFFORT)
    assert result.returncode == 0, result.stderr
    section = result.stdout.split("### Unsigned Manual Check\n", 1)[1].split("\n\n", 1)[0]
    listed = set(re.findall(r"^- \*\*(\S+)\*\*", section, flags=re.MULTILINE))
    assert listed == {
        f"{MIX}-{world.mix['manual-unsigned']}-0".lower(),
        "s-manual-unsigned-r1-0",
    }


def test_r1_agreement_every_surface_reports_one_status_per_requirement(
    world: World, client: TestClient
) -> None:
    expected = _expected_statuses(world)
    surfaces: list[Callable[[], Statuses]] = [
        lambda: _shared_operation(world),
        lambda: _view(world, "plan"),
        lambda: _dashboard_phase_route(client, world),
        lambda: _dashboard_requirement_route(client, expected),
    ]
    for read in surfaces:
        assert read() == expected


CLOSING_PHASE = "closing"
CLOSING_BODY = f"{PHASE_BODY}\n## Landing\n\nbranch: phase/{CLOSING_PHASE}\nbase: main\n"


def _closing_world(tmp_path: Path) -> tuple[Project, Path, str]:
    project = make_project(tmp_path)
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "base.txt").write_text("base\n")
    _git(tmp_path, "add", "base.txt")
    _git(tmp_path, "commit", "-qm", "base")
    _git(tmp_path, "branch", "-M", "main")
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    create(
        project,
        "score:phase",
        CLOSING_PHASE,
        {"title": CLOSING_PHASE, "ordinal": 1, "effort": EFFORT},
        CLOSING_BODY,
    )
    _git(tmp_path, "branch", f"phase/{CLOSING_PHASE}", "main")
    (tmp_path / ".worktrees").mkdir()
    tree = tmp_path / ".worktrees" / CLOSING_PHASE
    _git(tmp_path, "worktree", "add", "-q", str(tree), f"phase/{CLOSING_PHASE}")
    item = create(
        project,
        "score:work-item",
        "verify",
        {
            "title": "verify",
            "phase": CLOSING_PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "executor": "inline",
            "requirements": ["R1"],
        },
        "## Description\n\nR1: Behavior R1.\n\n## Approach\n\nVerify it.",
    )
    project.update(item["id"], record_type="score:work-item", payload={"assignee": "runner"})
    _acceptance(project, CLOSING_PHASE, "verify", "R1", "check")
    return project, tmp_path, _git(tree, "rev-parse", "HEAD")


@pytest.mark.parametrize(
    ("other_result", "expected"),
    [(None, "unverified"), ("fail", "failed"), ("pass", "verified")],
)
def test_r1_agreement_closing_task_close_follows_the_shared_operation(
    tmp_path: Path, other_result: str | None, expected: RequirementState
) -> None:
    project, root, revision = _closing_world(tmp_path)
    other = _acceptance(project, CLOSING_PHASE, "other", "R1", "check")
    if other_result is not None:
        _run(project, other, other_result, revision)

    started = wave.start(project, root, CLOSING_PHASE)

    assert started.runner is not None
    status = requirement_status(project.records(), CLOSING_PHASE)["R1"].status
    assert status == expected
    assert (started.runner.state == "done") == (status == "verified")
    item = project.resolve("score:work-item", "verify")
    assert (item["lifecycle_state"] == "done") == (status == "verified")
