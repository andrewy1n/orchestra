from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from canon_support import create, make_project

from dashboard.backend import phase as dashboard_phase
from dashboard.backend.phase import load_phase_detail
from dashboard.backend.snapshot import load_snapshot
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.canon.workspace import Workspace
from orchestra.conductor.landing import gate, land
from orchestra.conductor.landing import landing as landing_module
from orchestra.conductor.landing.landing import (
    Landing,
    LandingPlace,
    ProofPacket,
    latest_landing,
    phase_place,
    proof_packet,
)
from orchestra.conductor.phases.progress import close, phase_progress
from orchestra.conductor.phases.progress.phase_progress import open_phase_progress
from orchestra.conductor.phases.workflow import workflow
from orchestra.conductor.phases.workflow.workflow import preview_run, run_status, start_run
from orchestra.conductor.tasks import wave
from orchestra.metrics import phases as metrics_phases
from orchestra.metrics.phases import build_phase_rows
from orchestra.score.planning.phase import Phase, current_phase_model, read_phase
from orchestra.score.workflow import workflow_selection
from orchestra.tools.github import GitHubCheck
from orchestra.views import render as views

EFFORT = "ef"
PHASE = "feature"
ELSEWHERE = "elsewhere"
OTHER_EFFORT = "other-effort"
BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n"
STALE_SHA = "b" * 40


def _rid(group: int, number: int) -> str:
    return f"rec-{group:08x}-0000-0000-0000-{number:012x}"


PHASE_CURRENT = _rid(1, 4)
PHASE_TIE_LOSER = _rid(1, 3)
PHASE_CORRECTED = _rid(1, 2)
PHASE_SUPERSEDED = _rid(1, 1)

LANDING_NUMBERS = {number: _rid(2, number) for number in (1, 2, 3, 4, 9)}
LANDING_WINNER = LANDING_NUMBERS[4]

PACKET_FIX = _rid(3, 1)
PACKET_CORRECTED = _rid(3, 3)
PACKET_WINNER = _rid(3, 2)
PACKET_OLD = _rid(3, 0)
PACKET_OTHER_EFFORT = _rid(3, 4)
PACKET_ELSEWHERE = _rid(3, 5)


def _stamp(second: int) -> str:
    return f"2026-11-01T00:00:{second:02d}+00:00"


@dataclass
class Rig:
    project: Project
    head: str
    picks: Picks
    monkeypatch: pytest.MonkeyPatch

    @property
    def root(self) -> Path:
        return self.project.project_root


class Picks:
    def __init__(self) -> None:
        self.reader = ""
        self._found: dict[str, dict[str, set[str]]] = {}

    def add(self, kind: str, record_id: str) -> None:
        self._found.setdefault(self.reader, {}).setdefault(kind, set()).add(record_id)

    def of(self, reader: str, kind: str) -> set[str]:
        return self._found.get(reader, {}).get(kind, set())


Reader = Callable[[Rig], None]


@dataclass(frozen=True)
class Case:
    run: Reader
    state: str = "in_progress"
    landings: bool = True
    packets: bool = True


@dataclass
class FakeGh:
    head: str
    created: list[tuple[str, str]] = field(default_factory=lambda: [])

    def push_branch(self, remote: str, branch: str) -> None:
        pass

    def find_pull_request(self, head: str) -> tuple[int, str] | None:
        return None

    def create_pull_request(self, head: str, base: str, title: str, body: str) -> tuple[int, str]:
        self.created.append((title, body))
        return 7, "https://example.test/pull/7"

    def update_pull_request(self, number: int, title: str, body: str) -> None:
        raise AssertionError("no pull request exists to update")

    def head_sha(self, number: int) -> str:
        return self.head

    def checks(self, number: int) -> tuple[GitHubCheck, ...]:
        return (GitHubCheck("CI", "completed", "success"),)


@dataclass(frozen=True)
class MergedStates:
    head: str

    def pull_request_state(self, number: int) -> tuple[str, str]:
        return "MERGED", self.head


def _put(
    project: Project,
    record_type: str,
    record_id: str,
    subject: str,
    payload: JsonObject,
    *,
    at: str,
    state: str,
    body: str = "",
    relationships: dict[str, list[str]] | None = None,
) -> None:
    store, _ = project._session()
    record: Record = {
        "id": record_id,
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": relationships or {},
        "revision": "",
        "body": body,
        "recorded_at": at,
    }
    store.create_record(record)


def _phase_body(branch: str) -> str:
    return f"{BODY}\n## Landing\n\nBranch: {branch}\n"


def _put_phase(
    project: Project,
    record_id: str,
    *,
    at: str,
    state: str,
    ordinal: int,
    relationships: dict[str, list[str]] | None = None,
) -> None:
    payload: JsonObject = {
        "title": f"Title of {record_id}",
        "ordinal": ordinal,
        "effort": EFFORT,
        "weight": "full",
    }
    _put(
        project,
        "score:phase",
        record_id,
        PHASE,
        payload,
        at=at,
        state=state,
        body=_phase_body(f"branch/{record_id}"),
        relationships=relationships,
    )


def _put_landing(
    project: Project,
    record_id: str,
    number: int,
    *,
    at: str,
    result: str,
    head: str,
    effort: str | None,
    phase: str = PHASE,
    corrects: Sequence[str] = (),
) -> None:
    payload: JsonObject = {
        "phase": phase,
        "number": number,
        "url": f"https://example.test/pull/{number}",
        "head_sha": head,
        "result": result,
    }
    if effort is not None:
        payload["effort"] = effort
    _put(
        project,
        "conductor:landing",
        record_id,
        phase,
        payload,
        at=at,
        state="recorded",
        relationships={"corrects": list(corrects)} if corrects else None,
    )


def _put_packet(
    project: Project,
    record_id: str,
    head: str,
    *,
    at: str,
    effort: str | None,
    phase: str = PHASE,
    corrects: Sequence[str] = (),
) -> None:
    payload: JsonObject = {"phase": phase, "revision": head, "base": "main", "kind": "claims"}
    if effort is not None:
        payload["effort"] = effort
    _put(
        project,
        "conductor:proof-packet",
        record_id,
        phase,
        payload,
        at=at,
        state="recorded",
        body=f"## Look\n\npacket {record_id}\n\n## Machine\n\nm\n\n## Attention\n\nnone\n\n## Diff\n\nd\n",
        relationships={"corrects": list(corrects)} if corrects else None,
    )


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _build(root: Path, *, state: str, landings: bool, packets: bool) -> tuple[Project, str]:
    project = make_project(root)
    with (root / "orchestra.toml").open("a", encoding="utf-8") as policy:
        policy.write('\n[land]\nadapter = "github-pr"\nmerge = "human"\n')
    _git(root, "add", "orchestra.toml")
    _git(root, "commit", "-qm", "land policy")
    with (root / ".git" / "info" / "exclude").open("a", encoding="utf-8") as exclude:
        exclude.write(".canon/\n")
    head = _git(root, "rev-parse", "HEAD")
    create(project, "score:effort", EFFORT, {"goal": "Land", "kind": "deliver"})

    _put_phase(project, PHASE_SUPERSEDED, at=_stamp(9), state="superseded", ordinal=9)
    _put_phase(project, PHASE_CORRECTED, at=_stamp(9), state="planned", ordinal=8)
    _put_phase(
        project,
        PHASE_TIE_LOSER,
        at=_stamp(5),
        state="planned",
        ordinal=7,
        relationships={"corrects": [PHASE_CORRECTED]},
    )
    _put_phase(
        project,
        PHASE_CURRENT,
        at=_stamp(5),
        state=state,
        ordinal=1,
        relationships={"supersedes": [PHASE_SUPERSEDED]},
    )
    task = create(
        project,
        "score:work-item",
        "build-it",
        {"title": "Build", "phase": PHASE, "kind": "deliver", "assignee": "", "effort": EFFORT},
    )
    project.update(task["id"], transition="in_progress")
    project.update(task["id"], transition="done")

    if landings:
        _put_landing(
            project, LANDING_NUMBERS[3], 3, at=_stamp(5), result="fail", head=head, effort=EFFORT
        )
        _put_landing(
            project, LANDING_WINNER, 4, at=_stamp(5), result="success", head=head, effort=None
        )
        _put_landing(
            project,
            LANDING_NUMBERS[2],
            2,
            at=_stamp(2),
            result="success",
            head=head,
            effort=None,
            corrects=[LANDING_NUMBERS[1]],
        )
        _put_landing(
            project,
            LANDING_NUMBERS[1],
            1,
            at=_stamp(1),
            result="fail",
            head=STALE_SHA,
            effort=EFFORT,
        )
        _put_landing(
            project,
            LANDING_NUMBERS[9],
            9,
            at=_stamp(9),
            result="fail",
            head=STALE_SHA,
            effort=None,
            phase=ELSEWHERE,
        )
    if packets:
        _put_packet(project, PACKET_CORRECTED, head, at=_stamp(8), effort=EFFORT)
        _put_packet(
            project, PACKET_FIX, head, at=_stamp(8), effort=EFFORT, corrects=[PACKET_CORRECTED]
        )
        _put_packet(project, PACKET_WINNER, head, at=_stamp(8), effort=None)
        _put_packet(project, PACKET_OLD, head, at=_stamp(3), effort=EFFORT)
        _put_packet(project, PACKET_OTHER_EFFORT, head, at=_stamp(9), effort=OTHER_EFFORT)
        _put_packet(project, PACKET_ELSEWHERE, head, at=_stamp(9), effort=EFFORT, phase=ELSEWHERE)
    return project, head


def _install(monkeypatch: pytest.MonkeyPatch, picks: Picks) -> None:
    def current(slug: str, records: Sequence[Record]) -> Phase | None:
        found = current_phase_model(slug, records)
        if found is not None:
            picks.add("phase", found.id)
        return found

    def read(record: Record) -> Phase:
        found = read_phase(record)
        picks.add("phase", found.id)
        return found

    def place(phase: Phase, store: Path) -> LandingPlace:
        picks.add("phase", phase.id)
        return phase_place(phase, store)

    def latest(records: Sequence[Record], phase: str) -> Landing | None:
        found = latest_landing(records, phase)
        if found is not None:
            picks.add("landing", found.id)
        return found

    def packet(
        records: Sequence[Record], phase: Phase, head: str | None = None
    ) -> ProofPacket | None:
        found = proof_packet(records, phase, head)
        if found is not None:
            picks.add("packet", found.id)
        return found

    for module in (
        workflow,
        gate,
        close,
        land,
        metrics_phases,
        dashboard_phase,
    ):
        monkeypatch.setattr(module, "current_phase_model", current)
    for module in (wave, dashboard_phase, workflow_selection, phase_progress):
        monkeypatch.setattr(module, "read_phase", read)
    for module in (gate, close, wave, phase_progress):
        monkeypatch.setattr(module, "phase_place", place)
    for module in (close, metrics_phases, landing_module):
        monkeypatch.setattr(module, "latest_landing", latest)
    for module in (
        phase_progress,
        land,
        metrics_phases,
        dashboard_phase,
        landing_module,
    ):
        monkeypatch.setattr(module, "proof_packet", packet)


def _through_workflow(rig: Rig) -> None:
    preview = preview_run(rig.project, EFFORT, PHASE, "single-step", step="land")
    run = start_run(rig.project, preview)
    run_status(rig.project, run["subject"])


def _through_gate(rig: Rig) -> None:
    gate.gate_terms(rig.project, PHASE)


def _through_close(rig: Rig) -> None:
    result = close.close_phase(
        rig.project,
        rig.root,
        PHASE,
        MergedStates(rig.head),
        reconcile_architecture=lambda *_: False,
    )
    rig.picks.add("landing", LANDING_NUMBERS[result.number])


def _through_wave(rig: Rig) -> None:
    wave.end(rig.project, rig.root, PHASE)


def _through_handoff(rig: Rig) -> None:
    records = views.load_records(rig.project)
    views.render_view(
        views.VIEWS["handoff"], records, progress=open_phase_progress(rig.project, records)
    )


def _through_metrics(rig: Rig) -> None:
    build_phase_rows(rig.root)


def _through_snapshot(rig: Rig) -> None:
    view = next(view for view in load_snapshot(rig.project).efforts if view.effort == EFFORT)
    row = next(row for row in view.phases if row.subject == PHASE)
    rig.picks.add("phase", row.id)


def _through_phase_detail(rig: Rig) -> None:
    detail = load_phase_detail(rig.project, EFFORT, PHASE)
    if detail.proof is not None:
        rig.picks.add("packet", detail.proof.id)


def _through_land(rig: Rig) -> None:
    def no_terms(*args: object, **kwargs: object) -> list[gate.Term]:
        return []

    client = FakeGh(rig.head)
    with rig.monkeypatch.context() as patch:
        patch.setattr(gate, "gate_terms", no_terms)
        land.land_phase(
            Workspace(rig.root),
            PHASE,
            rig.root,
            client,
            base="main",
            remote="origin",
            poll_interval_s=1,
            timeout_s=10,
        )
    body = client.created[0][1]
    found = re.search(r"packet (rec-\S+)", body)
    assert found is not None
    rig.picks.add("packet", found.group(1))


def _drive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cases: dict[str, Case]) -> Picks:
    picks = Picks()
    _install(monkeypatch, picks)
    for name, case in cases.items():
        picks.reader = name
        project, head = _build(
            tmp_path / name, state=case.state, landings=case.landings, packets=case.packets
        )
        case.run(Rig(project, head, picks, monkeypatch))
    return picks


def _agreed(picks: Picks, cases: dict[str, Case], kind: str) -> dict[str, set[str]]:
    return {name: picks.of(name, kind) for name in cases}


R1_CASES = {
    "workflow": Case(_through_workflow),
    "gate": Case(_through_gate),
    "close": Case(_through_close),
    "wave": Case(_through_wave),
    "handoff": Case(_through_handoff),
    "metrics": Case(_through_metrics, state="done"),
    "dashboard-snapshot": Case(_through_snapshot),
    "dashboard-detail": Case(_through_phase_detail),
}

R5_CASES = {
    "workflow": Case(_through_workflow, packets=False),
    "handoff": Case(_through_handoff, packets=False),
    "close": Case(_through_close, packets=False),
    "metrics": Case(_through_metrics, state="done", packets=False),
}

R7_CASES = {
    "land": Case(_through_land, landings=False),
    "workflow": Case(_through_workflow),
    "metrics": Case(_through_metrics, state="done", landings=False),
    "dashboard-detail": Case(_through_phase_detail, landings=False),
}


def test_r1_every_reader_selects_the_same_current_phase_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    picks = _drive(tmp_path, monkeypatch, R1_CASES)

    assert _agreed(picks, R1_CASES, "phase") == {name: {PHASE_CURRENT} for name in R1_CASES}


def test_r5_every_reader_selects_the_same_latest_landing_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    picks = _drive(tmp_path, monkeypatch, R5_CASES)

    assert _agreed(picks, R5_CASES, "landing") == {name: {LANDING_WINNER} for name in R5_CASES}


def test_r5_dashboard_reads_the_latest_landing_through_the_progress_model_and_exposes_no_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    picks = _drive(tmp_path, monkeypatch, {"dashboard": Case(_through_phase_detail)})
    project, _ = _build(tmp_path / "view", state="in_progress", landings=True, packets=False)

    shown = repr(load_snapshot(project)) + repr(load_phase_detail(project, EFFORT, PHASE))

    assert picks.of("dashboard", "landing") == {LANDING_WINNER}
    assert not [record_id for record_id in LANDING_NUMBERS.values() if record_id in shown]


def test_r7_every_reader_selects_the_same_latest_belonging_proof_packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    picks = _drive(tmp_path, monkeypatch, R7_CASES)

    assert _agreed(picks, R7_CASES, "packet") == {name: {PACKET_WINNER} for name in R7_CASES}
