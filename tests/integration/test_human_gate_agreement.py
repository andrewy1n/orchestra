from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pytest
from canon_support import make_project

from dashboard.backend.server import service
from orchestra import views
from orchestra.canon import project as project_mod
from orchestra.canon import record as record_mod
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor import gate

EFFORT = "alpha"
PHASE = "p1"
NOW = datetime(2030, 1, 2, tzinfo=timezone.utc)
SHARED_KINDS = ("blocking-question", "needs-human", "unsigned-check")
HANDOFF_ROLES = {
    "blocking-question": "Blocking Question",
    "needs-human": "Needs Human",
    "unsigned-check": "Unsigned Manual Check",
}
GATE_PREFIXES = {
    "blocking-question": "question-needs-human:",
    "needs-human": "finding-needs-human:",
    "unsigned-check": "manual-check-signed:",
}


class Stamps:
    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.count = 0
        monkeypatch.setattr(record_mod, "now", self.next)
        monkeypatch.setattr(project_mod, "now", self.next)

    def next(self) -> str:
        self.count += 1
        return f"2030-01-01T{self.count // 3600:02d}:{self.count // 60 % 60:02d}:{self.count % 60:02d}+00:00"


def _create(project: Project, record_type: str, subject: str, payload: JsonObject) -> Record:
    sections = project.schemas().types[record_type].sections
    body = "\n\n".join(f"## {name}\n\nText." for name in sections)
    return project.create(record_type=record_type, subject=subject, payload=payload, body=body)


def _question(project: Project, subject: str, *, blocking: bool) -> Record:
    payload: JsonObject = {"scope": subject, "owner": "human", "blocking": blocking}
    return _create(project, "score:continuity-question", subject, payload)


def _finding(project: Project, subject: str, needs: str) -> Record:
    payload: JsonObject = {
        "claim": f"claim of {subject}",
        "basis": "observed",
        "needs": needs,
        "effort": EFFORT,
        "invalidated_when": "decision recorded",
    }
    return _create(project, "tuner:finding", subject, payload)


def _acceptance(project: Project, subject: str) -> Record:
    payload: JsonObject = {
        "method": "manual",
        "effort": EFFORT,
        "phase": PHASE,
        "verify_command": "true",
    }
    return _create(project, "score:acceptance", subject, payload)


def _run(project: Project, subject: str, criterion: str, signed_by: str) -> Record:
    payload: JsonObject = {
        "criterion_id": criterion,
        "revision": "abc",
        "result": "pass",
        "effort": EFFORT,
        "method": "manual",
        "signed_by": signed_by,
    }
    return _create(project, "tuner:check-run", subject, payload)


def _gate_ids(project: Project, subject_ids: dict[str, str], kinds: tuple[str, ...]) -> set[str]:
    terms = gate.gate_terms(project.project_root, PHASE)
    ids: set[str] = set()
    for kind in kinds:
        prefix = GATE_PREFIXES[kind]
        ids.update(
            subject_ids[term.name.removeprefix(prefix)]
            for term in terms
            if term.name.startswith(prefix) and not term.holds
        )
    return ids


def _handoff_ids(project: Project, kinds: tuple[str, ...]) -> set[str]:
    text = views.render_view(views.HANDOFF, views.load_records(project), effort=EFFORT)
    ids: set[str] = set()
    for section in text.split("### ")[1:]:
        title, _, rest = section.partition("\n")
        if title in {HANDOFF_ROLES[kind] for kind in kinds}:
            ids.update(re.findall(r"id: (\S+?)\)", rest.split("\n\n", 1)[0]))
    return ids


def _dashboard_ids(project: Project, kinds: tuple[str, ...]) -> set[str]:
    snapshot = service.Reader(project).cache.work_current(NOW)
    return {
        item.id
        for view in snapshot.efforts
        if view.effort == EFFORT
        for item in view.needs_you
        if item.kind in kinds
    }


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Project, dict[str, str]]:
    Stamps(monkeypatch)
    project = make_project(tmp_path)
    _create(project, "score:effort", EFFORT, {"goal": "ship alpha", "kind": "deliver"})
    _create(project, "score:phase", PHASE, {"title": "Phase one", "ordinal": 1, "effort": EFFORT})
    ids = {
        "blocking": _question(project, EFFORT, blocking=True)["id"],
        "open": _question(project, EFFORT, blocking=False)["id"],
        "finding": _finding(project, "needs-human-f", "human")["id"],
    }
    _finding(project, "agent-f", "agent")
    _acceptance(project, "unsigned-a")
    ids["unsigned"] = _run(project, "unsigned-run", "unsigned-a", "")["id"]
    _acceptance(project, "signed-later-a")
    ids["stale"] = _run(project, "stale-run", "signed-later-a", "")["id"]
    _run(project, "signed-run", "signed-later-a", "alice")
    subject_ids = {
        EFFORT: ids["blocking"],
        "needs-human-f": ids["finding"],
        "unsigned-a": ids["unsigned"],
    }
    project_ids = dict(subject_ids)
    project_ids["open"] = ids["open"]
    project_ids["stale"] = ids["stale"]
    return project, project_ids


@pytest.mark.parametrize(
    "kinds",
    [
        SHARED_KINDS,
        ("blocking-question",),
        ("needs-human",),
        ("unsigned-check",),
        ("blocking-question", "unsigned-check"),
    ],
)
def test_r8_agreement_across_gate_handoff_and_dashboard(
    store: tuple[Project, dict[str, str]], kinds: tuple[str, ...]
) -> None:
    project, ids = store
    expected_by_kind = {
        "blocking-question": ids[EFFORT],
        "needs-human": ids["needs-human-f"],
        "unsigned-check": ids["unsigned-a"],
    }
    expected = {expected_by_kind[kind] for kind in kinds}

    from_gate = _gate_ids(project, ids, kinds)
    from_handoff = _handoff_ids(project, kinds)
    from_dashboard = _dashboard_ids(project, kinds)

    assert from_gate == from_handoff == from_dashboard == expected
    assert ids["stale"] not in from_gate | from_handoff | from_dashboard


def test_r8_dashboard_alone_lists_the_open_question(
    store: tuple[Project, dict[str, str]],
) -> None:
    project, ids = store
    everything = _dashboard_ids(project, (*SHARED_KINDS, "open-question"))

    assert ids["open"] in everything
    assert ids["open"] not in _gate_ids(project, ids, SHARED_KINDS)
    assert ids["open"] not in _handoff_ids(project, SHARED_KINDS)
