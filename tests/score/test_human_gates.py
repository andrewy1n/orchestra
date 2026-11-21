from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import create, make_project

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.phase_progress import _gates as progress_gates
from orchestra.score.phase import read_phase
from orchestra.score.workflow_blockers import (
    HumanGate,
    WorkflowBlocker,
    human_gates,
    is_open_finding,
    is_signed,
    latest_manual_check,
    phase_blockers,
    unsigned_manual_checks,
)

EFFORT = "alpha"
OTHER_EFFORT = "beta"
BLOCKING_KINDS = ("blocking-question", "needs-human")
QUESTION_STATES = ("open", "answered", "deferred", "closed")
FINDING_STATES = ("asserted", "supported", "disputed", "refuted", "retracted")
OPEN_FINDING_STATES = ("asserted", "supported", "disputed")
FINDING_PATH = {
    "asserted": [],
    "supported": ["supported"],
    "disputed": ["disputed"],
    "refuted": ["refuted"],
    "retracted": ["retracted"],
}
QUESTION_PATH = {
    "open": [],
    "answered": ["answered"],
    "deferred": ["deferred"],
    "closed": ["closed"],
}


@pytest.fixture
def project(tmp_path: Path) -> Project:
    store = make_project(tmp_path)
    for effort in (EFFORT, OTHER_EFFORT):
        create(store, "score:effort", effort, {"goal": f"Goal {effort}", "kind": "deliver"})
    return store


def _phase(
    project: Project, slug: str, ordinal: int, effort: str = EFFORT, **extra: object
) -> None:
    create(
        project,
        "score:phase",
        slug,
        {"title": slug, "ordinal": ordinal, "effort": effort, **extra},
    )


def _find(project: Project, record: Record) -> Record:
    return next(item for item in _stored(project) if item["id"] == record["id"])


def _finding(
    project: Project,
    subject: str,
    *,
    needs: str = "human",
    state: str = "asserted",
    effort: str = EFFORT,
    phase: str | None = None,
) -> Record:
    payload: dict[str, object] = {
        "claim": "Claim.",
        "basis": "Basis.",
        "invalidated_when": "Never.",
        "effort": effort,
        "needs": needs,
    }
    if phase is not None:
        payload["phase"] = phase
    record = create(project, "tuner:finding", subject, payload)
    for step in FINDING_PATH[state]:
        project.update(record["id"], transition=step)
    return _find(project, record)


def _without_payload_key(record: Record, key: str) -> Record:
    stripped = record.copy()
    stripped["payload"] = {name: value for name, value in record["payload"].items() if name != key}
    return stripped


def _without_effort(record: Record) -> Record:
    return _without_payload_key(record, "effort")


def _question(
    project: Project,
    subject: str,
    *,
    blocking: bool | None,
    state: str = "open",
    phase: str | None = None,
) -> Record:
    payload: dict[str, object] = {"owner": "me", "blocking": bool(blocking), "scope": "all"}
    if phase is not None:
        payload["phase"] = phase
    record = create(project, "score:continuity-question", subject, payload)
    for step in QUESTION_PATH[state]:
        project.update(record["id"], transition=step)
    stored = _find(project, record)
    if blocking is None:
        return _without_payload_key(stored, "blocking")
    return stored


def _acceptance(project: Project, subject: str = "accept-one") -> Record:
    return create(
        project,
        "score:acceptance",
        subject,
        {"method": "manual", "effort": EFFORT, "verify_command": "true"},
    )


_STAMPS: dict[str, str] = {}


def _run(
    project: Project,
    acceptance: Record,
    *,
    signed_by: str = "",
    method: str = "manual",
    by_subject: bool = False,
) -> Record:
    criterion = acceptance["subject"] if by_subject else acceptance["id"]
    run = create(
        project,
        "tuner:check-run",
        acceptance["subject"],
        {
            "criterion_id": criterion,
            "revision": "abc",
            "result": "pass",
            "effort": EFFORT,
            "method": method,
            "signed_by": signed_by,
        },
    )
    stamp = _next_stamp()
    _STAMPS[run["id"]] = stamp
    stamped = run.copy()
    stamped["recorded_at"] = stamp
    return stamped


def _correct(project: Project, record_id: str, *, payload: JsonObject) -> Record:
    result = project.correct(record_id, payload=payload)
    corrected = result["record"]
    _STAMPS[corrected["id"]] = _next_stamp()
    return corrected


def _next_stamp() -> str:
    return f"2030-01-01T00:{len(_STAMPS) // 60:02d}:{len(_STAMPS) % 60:02d}+00:00"


def _stored(project: Project) -> list[Record]:
    stored: list[Record] = []
    for record in project.records():
        stamp = _STAMPS.get(record["id"])
        if stamp is not None:
            record = record.copy()
            record["recorded_at"] = stamp
        stored.append(record)
    return stored


def _gates(records: list[Record], kind: str) -> list[HumanGate]:
    return [gate for gate in human_gates(records) if gate.kind == kind]


def _ids(gates: list[HumanGate]) -> list[str]:
    return [gate.record["id"] for gate in gates]


@pytest.mark.parametrize("state", QUESTION_STATES)
def test_r1_blocking_question_gate_follows_open_state(project: Project, state: str) -> None:
    question = _question(project, EFFORT, blocking=True, state=state)

    assert _ids(_gates([question], "blocking-question")) == (
        [question["id"]] if state == "open" else []
    )


def test_r1_blocking_question_is_not_an_open_question(project: Project) -> None:
    question = _question(project, EFFORT, blocking=True)

    assert _gates([question], "open-question") == []


@pytest.mark.parametrize("state", QUESTION_STATES)
@pytest.mark.parametrize("blocking", [False, None])
def test_r2_non_blocking_question_gate_follows_open_state(
    project: Project, state: str, blocking: bool | None
) -> None:
    question = _question(project, EFFORT, blocking=blocking, state=state)

    assert _ids(_gates([question], "open-question")) == (
        [question["id"]] if state == "open" else []
    )
    assert _gates([question], "blocking-question") == []


@pytest.mark.parametrize("state", FINDING_STATES)
def test_r3_needs_human_finding_gate_follows_lifecycle(project: Project, state: str) -> None:
    finding = _finding(project, "needs-human", state=state)

    assert is_open_finding(finding) is (state in OPEN_FINDING_STATES)
    assert _ids(_gates([finding], "needs-human")) == (
        [finding["id"]] if state in OPEN_FINDING_STATES else []
    )


@pytest.mark.parametrize("state", FINDING_STATES)
def test_r3_finding_that_needs_none_is_never_a_gate(project: Project, state: str) -> None:
    finding = _finding(project, "needs-none", needs="none", state=state)

    assert _gates([finding], "needs-human") == []


def test_r3_open_finding_ignores_other_record_types(project: Project) -> None:
    question = _question(project, EFFORT, blocking=True)

    assert is_open_finding(question) is False


def test_r4_finding_without_effort_is_a_gate(project: Project) -> None:
    finding = _without_effort(_finding(project, "no-effort"))

    assert _ids(_gates([finding], "needs-human")) == [finding["id"]]


def test_r4_finding_with_effort_is_a_gate(project: Project) -> None:
    finding = _finding(project, "with-effort")

    assert _ids(_gates([finding], "needs-human")) == [finding["id"]]


def test_r4_resolved_finding_without_effort_is_not_a_gate(project: Project) -> None:
    finding = _without_effort(_finding(project, "no-effort-refuted", state="refuted"))

    assert _gates([finding], "needs-human") == []


def test_r5_latest_manual_check_is_the_only_run(project: Project) -> None:
    acceptance = _acceptance(project)
    run = _run(project, acceptance)

    latest = latest_manual_check(acceptance, _stored(project))

    assert latest is not None
    assert latest["id"] == run["id"]


def test_r5_latest_manual_check_is_the_later_run(project: Project) -> None:
    acceptance = _acceptance(project)
    _run(project, acceptance)
    later = _run(project, acceptance, signed_by="me")

    latest = latest_manual_check(acceptance, _stored(project))

    assert latest is not None
    assert latest["id"] == later["id"]


def test_r5_latest_manual_check_skips_corrected_run(project: Project) -> None:
    acceptance = _acceptance(project)
    first = _run(project, acceptance)
    second = _run(project, acceptance, signed_by="me")
    _correct(project, second["id"], payload={"signed_by": ""})
    records = _stored(project)

    latest = latest_manual_check(acceptance, records)

    assert latest is not None
    assert latest["id"] not in {second["id"], first["id"]}


def test_r5_latest_manual_check_ignores_non_manual_runs(project: Project) -> None:
    acceptance = _acceptance(project)
    manual = _run(project, acceptance)
    _run(project, acceptance, method="check")

    latest = latest_manual_check(acceptance, _stored(project))

    assert latest is not None
    assert latest["id"] == manual["id"]


def test_r5_latest_manual_check_matches_run_recorded_against_subject(project: Project) -> None:
    acceptance = _acceptance(project)
    run = _run(project, acceptance, by_subject=True)

    latest = latest_manual_check(acceptance, _stored(project))

    assert latest is not None
    assert latest["id"] == run["id"]


def test_r5_latest_manual_check_is_none_without_runs(project: Project) -> None:
    acceptance = _acceptance(project)

    assert latest_manual_check(acceptance, _stored(project)) is None


def test_r6_single_unsigned_run_is_a_gate(project: Project) -> None:
    acceptance = _acceptance(project)
    run = _run(project, acceptance)

    assert [item["id"] for item in unsigned_manual_checks(_stored(project))] == [run["id"]]
    assert _ids(_gates(_stored(project), "unsigned-check")) == [run["id"]]


def test_r6_single_signed_run_is_not_a_gate(project: Project) -> None:
    acceptance = _acceptance(project)
    _run(project, acceptance, signed_by="me")

    assert unsigned_manual_checks(_stored(project)) == []
    assert _gates(_stored(project), "unsigned-check") == []


def test_r6_unsigned_non_manual_run_is_not_a_gate(project: Project) -> None:
    acceptance = _acceptance(project)
    _run(project, acceptance, method="check")

    assert _gates(_stored(project), "unsigned-check") == []


def test_r6_unsigned_run_recorded_against_subject_is_a_gate(project: Project) -> None:
    acceptance = _acceptance(project)
    run = _run(project, acceptance, by_subject=True)

    assert _ids(_gates(_stored(project), "unsigned-check")) == [run["id"]]


def test_r6_signed_run_after_unsigned_run_clears_the_gate(project: Project) -> None:
    acceptance = _acceptance(project)
    _run(project, acceptance)
    _run(project, acceptance, signed_by="me")

    assert _gates(_stored(project), "unsigned-check") == []


def test_r6_unsigned_run_after_signed_run_is_a_gate(project: Project) -> None:
    acceptance = _acceptance(project)
    _run(project, acceptance, signed_by="me")
    unsigned = _run(project, acceptance)

    assert _ids(_gates(_stored(project), "unsigned-check")) == [unsigned["id"]]


def test_r6_unsigned_run_corrected_by_signed_run_is_not_a_gate(project: Project) -> None:
    acceptance = _acceptance(project)
    run = _run(project, acceptance)
    _correct(project, run["id"], payload={"signed_by": "me"})

    assert _gates(_stored(project), "unsigned-check") == []


def test_r6_unsigned_run_corrected_by_unsigned_run_gates_the_correction_only(
    project: Project,
) -> None:
    acceptance = _acceptance(project)
    run = _run(project, acceptance)
    result = _correct(project, run["id"], payload={"result": "fail"})

    assert _ids(_gates(_stored(project), "unsigned-check")) == [result["id"]]


def test_r6_each_acceptance_has_its_own_gate(project: Project) -> None:
    first = _acceptance(project, "accept-one")
    second = _acceptance(project, "accept-two")
    first_run = _run(project, first)
    second_run = _run(project, second)

    assert sorted(_ids(_gates(_stored(project), "unsigned-check"))) == sorted(
        [first_run["id"], second_run["id"]]
    )


def test_r7_earlier_unsigned_run_is_not_a_gate(project: Project) -> None:
    acceptance = _acceptance(project)
    earlier = _run(project, acceptance)
    later = _run(project, acceptance)

    assert earlier["id"] not in _ids(_gates(_stored(project), "unsigned-check"))
    assert _ids(_gates(_stored(project), "unsigned-check")) == [later["id"]]


def test_r7_earlier_unsigned_run_by_subject_is_not_a_gate(project: Project) -> None:
    acceptance = _acceptance(project)
    _run(project, acceptance, by_subject=True)
    _run(project, acceptance, signed_by="me")

    assert unsigned_manual_checks(_stored(project)) == []


def test_r8_blocking_question_gate_reports_kind_record_and_clearing_type(
    project: Project,
) -> None:
    question = _question(project, EFFORT, blocking=True)

    assert human_gates([question]) == [
        HumanGate("blocking-question", question, "score:continuity-question")
    ]


def test_r8_open_question_gate_reports_kind_record_and_clearing_type(project: Project) -> None:
    question = _question(project, EFFORT, blocking=False)

    assert human_gates([question]) == [
        HumanGate("open-question", question, "score:continuity-question")
    ]


def test_r8_needs_human_gate_reports_kind_record_and_clearing_type(project: Project) -> None:
    finding = _finding(project, "needs-human")

    assert human_gates([finding]) == [HumanGate("needs-human", finding, "tuner:finding")]


def test_r8_unsigned_check_gate_reports_kind_record_and_clearing_type(project: Project) -> None:
    acceptance = _acceptance(project)
    run = _run(project, acceptance)

    assert human_gates(_stored(project)) == [HumanGate("unsigned-check", run, "tuner:check-run")]


def test_r8_one_store_yields_one_gate_of_each_kind(project: Project) -> None:
    blocking = _question(project, EFFORT, blocking=True)
    open_question = _question(project, OTHER_EFFORT, blocking=False)
    finding = _finding(project, "needs-human")
    run = _run(project, _acceptance(project))

    gates = human_gates(_stored(project))

    assert sorted((gate.kind, gate.record["id"]) for gate in gates) == sorted(
        [
            ("blocking-question", blocking["id"]),
            ("open-question", open_question["id"]),
            ("needs-human", finding["id"]),
            ("unsigned-check", run["id"]),
        ]
    )


def _blocked(project: Project, phase: str) -> list[WorkflowBlocker]:
    return phase_blockers(_stored(project), phase)


def _blocker_subjects(project: Project, phase: str) -> list[str]:
    return sorted(item.record["subject"] for item in _blocked(project, phase))


def _gate_ids(project: Project, kinds: tuple[str, ...] = BLOCKING_KINDS) -> set[str]:
    return {gate.record["id"] for gate in human_gates(_stored(project)) if gate.kind in kinds}


def _assert_blockers_are_gates(project: Project, phase: str) -> None:
    blocker_ids = {item.record["id"] for item in _blocked(project, phase)}
    assert blocker_ids <= _gate_ids(project)


@pytest.fixture
def phases(project: Project) -> None:
    _phase(project, "base", 1)
    _phase(project, "mid", 2, depends_on=["base"])
    _phase(project, "side", 3)
    _phase(project, "foreign", 1, effort=OTHER_EFFORT)


def test_r9_finding_on_the_phase_blocks_it(project: Project, phases: None) -> None:
    _finding(project, "on-mid", phase="mid")

    assert _blocker_subjects(project, "mid") == ["on-mid"]
    _assert_blockers_are_gates(project, "mid")


def test_r9_finding_on_a_dependency_phase_blocks_the_dependent(
    project: Project, phases: None
) -> None:
    _finding(project, "on-base", phase="base")

    assert _blocker_subjects(project, "mid") == ["on-base"]
    _assert_blockers_are_gates(project, "mid")


def test_r9_finding_on_another_phase_of_the_effort_does_not_block(
    project: Project, phases: None
) -> None:
    _finding(project, "on-side", phase="side")

    assert _blocker_subjects(project, "mid") == []
    assert _blocker_subjects(project, "side") == ["on-side"]


def test_r9_finding_on_another_effort_does_not_block(project: Project, phases: None) -> None:
    _finding(project, "on-foreign", effort=OTHER_EFFORT, phase="foreign")

    assert _blocker_subjects(project, "mid") == []
    assert _blocker_subjects(project, "foreign") == ["on-foreign"]
    _assert_blockers_are_gates(project, "foreign")


def test_r9_effort_finding_without_phase_blocks_every_phase_of_its_effort(
    project: Project, phases: None
) -> None:
    _finding(project, "effort-wide")

    assert _blocker_subjects(project, "mid") == ["effort-wide"]
    assert _blocker_subjects(project, "side") == ["effort-wide"]
    assert _blocker_subjects(project, "foreign") == []
    _assert_blockers_are_gates(project, "side")


def test_r9_blocking_question_blocks_its_effort(project: Project, phases: None) -> None:
    _question(project, EFFORT, blocking=True)

    assert _blocker_subjects(project, "mid") == [EFFORT]
    assert _blocker_subjects(project, "foreign") == []
    _assert_blockers_are_gates(project, "mid")


def test_r9_blocking_question_on_a_dependency_phase_blocks_the_dependent(
    project: Project, phases: None
) -> None:
    _question(project, EFFORT, blocking=True, phase="base")

    assert _blocker_subjects(project, "mid") == [EFFORT]
    assert _blocker_subjects(project, "side") == []
    _assert_blockers_are_gates(project, "mid")


def test_r9_open_question_does_not_block(project: Project, phases: None) -> None:
    _question(project, EFFORT, blocking=False)

    assert _blocker_subjects(project, "mid") == []
    assert _gate_ids(project, ("open-question",))


def test_r9_unsigned_check_does_not_block(project: Project, phases: None) -> None:
    _run(project, _acceptance(project))

    assert _blocker_subjects(project, "mid") == []
    assert _gate_ids(project, ("unsigned-check",))


@pytest.mark.parametrize("state", FINDING_STATES)
def test_r9_finding_blocks_only_while_open(project: Project, phases: None, state: str) -> None:
    _finding(project, "stateful", phase="mid", state=state)

    expected = ["stateful"] if state in OPEN_FINDING_STATES else []
    assert _blocker_subjects(project, "mid") == expected
    assert bool(_gate_ids(project)) is bool(expected)


@pytest.mark.parametrize("state", QUESTION_STATES)
def test_r9_blocking_question_blocks_only_while_open(
    project: Project, phases: None, state: str
) -> None:
    _question(project, EFFORT, blocking=True, state=state)

    expected = [EFFORT] if state == "open" else []
    assert _blocker_subjects(project, "mid") == expected
    assert bool(_gate_ids(project)) is bool(expected)


def test_r9_finding_that_needs_none_does_not_block(project: Project, phases: None) -> None:
    _finding(project, "needs-none", needs="none", phase="mid")

    assert _blocker_subjects(project, "mid") == []


def test_r9_blocking_question_stays_ahead_of_a_later_finding(
    project: Project, phases: None
) -> None:
    _question(project, EFFORT, blocking=True, phase="mid")
    _finding(project, "later-finding", phase="mid")
    records = _stored(project)

    assert [item.record["subject"] for item in phase_blockers(records, "mid")] == [
        EFFORT,
        "later-finding",
    ]
    phase = read_phase(
        next(
            record
            for record in records
            if record["record_type"] == "score:phase" and record["subject"] == "mid"
        )
    )
    text = "human gate: " + ", ".join(item.subject for item in progress_gates(records, phase))
    assert text == "human gate: alpha, later-finding"


def test_r9_blocker_scope_and_phase_are_unchanged(project: Project, phases: None) -> None:
    _finding(project, "on-base", phase="base")
    _finding(project, "effort-wide")

    def found(subject: str) -> WorkflowBlocker:
        return next(item for item in _blocked(project, "mid") if item.record["subject"] == subject)

    assert (found("on-base").scope, found("on-base").phase) == ("phase", "base")
    assert (found("effort-wide").scope, found("effort-wide").phase) == ("effort", None)


def _without_acceptances(project: Project) -> list[Record]:
    return [item for item in _stored(project) if item["record_type"] != "score:acceptance"]


def test_r6_unsigned_run_without_an_acceptance_is_a_gate(project: Project) -> None:
    acceptance = _acceptance(project)
    run = _run(project, acceptance)

    assert _ids(_gates(_without_acceptances(project), "unsigned-check")) == [run["id"]]


def test_r7_earlier_unsigned_run_without_an_acceptance_is_not_a_gate(project: Project) -> None:
    acceptance = _acceptance(project)
    _run(project, acceptance)
    later = _run(project, acceptance, signed_by="me")

    assert later["id"] not in _ids(_gates(_without_acceptances(project), "unsigned-check"))
    assert _gates(_without_acceptances(project), "unsigned-check") == []


def test_r6_unsigned_runs_without_a_criterion_are_each_a_gate(project: Project) -> None:
    acceptance = _acceptance(project)
    first = _run(project, acceptance)
    second = _run(project, acceptance, signed_by="me")
    records: list[Record] = []
    for item in _without_acceptances(project):
        if item["id"] in {first["id"], second["id"]}:
            blank = item.copy()
            blank["payload"] = {**item["payload"], "criterion_id": ""}
            records.append(blank)

    assert _ids(_gates(records, "unsigned-check")) == [first["id"]]


def test_r6_whitespace_only_signature_is_unsigned_and_matches_the_gate_rule(
    project: Project,
) -> None:
    acceptance = _acceptance(project)
    run = _run(project, acceptance, signed_by="   ")

    assert is_signed(run) is False
    assert _ids(_gates(_stored(project), "unsigned-check")) == [run["id"]]
