from __future__ import annotations

import json
from pathlib import Path

import pytest
from canon_support import create, make_project, seed_effort

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.cli import main

PHASE = "p1"
EFFORT = "alpha"


class Store:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.project: Project = make_project(root)
        seed_effort(self.project, EFFORT, PHASE)
        self.item: Record = create(
            self.project,
            "score:work-item",
            "task-1",
            {
                "title": "Task",
                "phase": PHASE,
                "kind": "deliver",
                "assignee": "",
                "effort": EFFORT,
                "executor": "inline",
                "requirements": ["R1"],
            },
            "## Description\n\nd\n\n## Approach\n\na",
        )

    def acceptance(self, method: str) -> Record:
        return create(
            self.project,
            "score:acceptance",
            f"criterion-{method}",
            {
                "method": method,
                "phase": PHASE,
                "effort": EFFORT,
                "verify_command": "true",
                "requirement": "R1",
            },
        )

    def check_run(self, criterion: Record, result: str) -> Record:
        return self.project.create(
            record_type="tuner:check-run",
            subject="task-1",
            payload={
                "criterion_id": criterion["id"],
                "result": result,
                "effort": EFFORT,
                "method": "check",
                "signed_by": "",
                "revision": "deadbeef",
                "runner": "orchestra",
            },
            body="",
        )


@pytest.fixture
def store(tmp_path: Path) -> Store:
    return Store(tmp_path / "store")


def _request(store: Store, **over: object) -> JsonObject:
    request: JsonObject = {
        "subject": "task-1",
        "effort": EFFORT,
        "work_item_id": store.item["id"],
        "transition": "done",
        "acceptance_ids": [],
        "criteria": [],
    }
    for key, value in over.items():
        request[key] = value  # pyright: ignore[reportArgumentType]
    return request


def _check_request(store: Store, result: str = "pass", **over: object) -> JsonObject:
    criterion = store.acceptance("check")
    run = store.check_run(criterion, result)
    entry: JsonObject = {
        "criterion_id": criterion["id"],
        "method": "check",
        "check_run_id": run["id"],
        "result": result,
    }
    return _request(store, acceptance_ids=[criterion["id"]], criteria=[entry], **over)


def _close_batch(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    request: JsonObject | str,
    *extra: str,
) -> tuple[int, str, str]:
    path = tmp_path / "request.json"
    path.write_text(request if isinstance(request, str) else json.dumps(request), encoding="utf-8")
    capsys.readouterr()
    try:
        code = main(["close-batch", "--input", str(path), *extra])
    except SystemExit as exit_:
        code = exit_.code if isinstance(exit_.code, int) else 1
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _operations(out: str) -> list[JsonObject]:
    return [json.loads(line) for line in out.splitlines()]


def test_r13_prints_the_work_item_update_for_an_approved_check_request(
    store: Store,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(store.root)

    code, out, _ = _close_batch(tmp_path, capsys, _check_request(store))

    assert code == 0
    assert _operations(out) == [
        {
            "op": "update",
            "type": "score:work-item",
            "id": store.item["id"],
            "transition": "done",
            "expected_revision": "@current",
        }
    ]


def test_r13_writes_the_operations_to_the_out_file(
    store: Store,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(store.root)
    target = tmp_path / "ops.ndjson"

    code, out, _ = _close_batch(tmp_path, capsys, _check_request(store), "--out", str(target))

    assert code == 0
    assert out == ""
    assert [op["op"] for op in _operations(target.read_text(encoding="utf-8"))] == ["update"]


def test_r13_prints_a_check_run_create_for_a_manual_criterion(
    store: Store,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(store.root)
    criterion = store.acceptance("manual")
    request = _request(
        store,
        acceptance_ids=[criterion["id"]],
        execution_report_id="rec-er",
        criteria=[
            {
                "criterion_id": criterion["id"],
                "method": "manual",
                "result": "pass",
                "revision": "abc123",
                "signed_by": "reviewer",
            }
        ],
    )

    code, out, _ = _close_batch(tmp_path, capsys, request)

    assert code == 0
    create_op, update_op = _operations(out)
    assert create_op == {
        "op": "create",
        "type": "tuner:check-run",
        "subject": "task-1",
        "payload": {
            "criterion_id": criterion["id"],
            "revision": "abc123",
            "result": "pass",
            "effort": EFFORT,
            "method": "manual",
            "signed_by": "reviewer",
            "informed_by": [criterion["id"], "rec-er"],
        },
    }
    assert update_op["transition"] == "done"


def test_r13_prints_a_finding_create_with_the_phase_of_the_work_item(
    store: Store,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(store.root)
    finding = {"claim": "c", "basis": "b", "invalidated_when": "w", "body": "text"}
    request = _check_request(store, result="fail", finding=finding)

    code, out, _ = _close_batch(tmp_path, capsys, request)

    assert code == 0
    finding_op, update_op = _operations(out)
    assert finding_op == {
        "op": "create",
        "type": "tuner:finding",
        "subject": "task-1",
        "payload": {
            "claim": "c",
            "basis": "b",
            "invalidated_when": "w",
            "effort": EFFORT,
            "phase": PHASE,
            "needs": "human",
        },
        "body": "text",
    }
    assert update_op["op"] == "update"


def test_r13_prints_a_finding_create_with_the_phase_of_the_request(
    store: Store,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(store.root)
    finding = {"claim": "c", "basis": "b", "invalidated_when": "w", "body": "t", "phase": "other"}

    code, out, _ = _close_batch(tmp_path, capsys, _check_request(store, "fail", finding=finding))

    assert code == 0
    payload = _operations(out)[0]["payload"]
    assert isinstance(payload, dict)
    assert payload["phase"] == "other"


def test_r14_refuses_an_unmet_criterion_without_a_finding_with_exit_2(
    store: Store,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(store.root)
    request = _check_request(store, result="fail")
    ids = request["acceptance_ids"]

    code, out, err = _close_batch(tmp_path, capsys, request)

    assert code == 2
    assert out == ""
    assert err == (
        "close refused: closing to done with unmet or unverified criterion(s) "
        f"{ids} and no finding -- refusing. Either resolve those "
        "criteria first, or supply `finding` (claim, basis, "
        "invalidated_when, body) to close anyway.\n"
    )


def test_r14_reports_invalid_json_with_exit_1(
    store: Store,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(store.root)

    code, out, err = _close_batch(tmp_path, capsys, "{not json")

    assert code == 1
    assert out == ""
    assert err.startswith("close-request is not valid JSON: ")


MALFORMED = [
    ({"subject": None}, "missing field: 'subject'"),
    ({"acceptance_ids": "x"}, "missing field: 'acceptance_ids'"),
    ({"criteria": "x"}, "field 'criteria' must be a list"),
    ({"criteria": ["x"]}, "each criteria entry must be an object"),
    ({"criteria": [{"_provided_fields": []}]}, "field '_provided_fields' is reserved"),
    ({"criteria": [{"result": 1}]}, "criterion field 'result' must be a string"),
    ({"execution_report_id": 1}, "field 'execution_report_id' must be a string"),
    ({"finding": "x"}, "field 'finding' must be an object"),
    ({"finding": {"claim": "c"}}, "finding missing field: 'basis'"),
    (
        {"acceptance_ids": ["a"], "criteria": [{"criterion_id": "b", "method": "check"}]},
        "criteria entry 'b' is not in acceptance_ids ['a']",
    ),
    (
        {"acceptance_ids": ["a"], "criteria": [{"criterion_id": "a"}]},
        "criteria entry missing field: 'method'",
    ),
    (
        {"acceptance_ids": ["a"], "criteria": [{"criterion_id": "a", "method": "tdd"}]},
        "criteria entry 'a' method='tdd' must reference a runner-produced check_run_id "
        "(from orchestra check); do not invent pass/fail",
    ),
    (
        {"acceptance_ids": ["a"], "criteria": [{"criterion_id": "a", "method": "manual"}]},
        "criteria entry missing field: 'result'",
    ),
    (
        {"acceptance_ids": ["a"], "criteria": [{"criterion_id": "a", "method": "guess"}]},
        "criteria entry 'a' has unknown method 'guess'",
    ),
]


@pytest.mark.parametrize(("change", "text"), MALFORMED)
def test_r14_reports_a_malformed_request_with_exit_1(
    store: Store,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    change: dict[str, object],
    text: str,
) -> None:
    monkeypatch.chdir(store.root)
    request = _request(store)
    for key, value in change.items():
        if value is None:
            del request[key]
        else:
            request[key] = value  # pyright: ignore[reportArgumentType]

    code, out, err = _close_batch(tmp_path, capsys, request)

    assert code == 1
    assert out == ""
    assert err == f"close-request malformed: {text}\n"


def test_r15_uses_the_store_named_by_store_argument(
    store: Store,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    code, out, err = _close_batch(
        tmp_path, capsys, _check_request(store), "--store", str(store.root)
    )

    assert (code, err) == (0, "")
    assert [op["op"] for op in _operations(out)] == ["update"]


def test_r15_reads_the_bound_store_without_store_argument(
    store: Store,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(store.root)

    code, out, err = _close_batch(tmp_path, capsys, _check_request(store))

    assert (code, err) == (0, "")
    assert [op["op"] for op in _operations(out)] == ["update"]


def test_r15_refuses_a_check_run_the_named_store_does_not_hold(
    store: Store,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    other = Store(tmp_path / "other")
    monkeypatch.chdir(other.root)
    request = _check_request(store)

    code, _, err = _close_batch(tmp_path, capsys, request, "--store", str(other.root))

    assert code == 2
    assert err.startswith("close refused: ")


def test_r14_refuses_with_exit_2_when_no_store_resolves(
    store: Store,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.delenv("ORCHESTRA_STORE", raising=False)
    monkeypatch.delenv("CANON_STORE", raising=False)

    code, out, err = _close_batch(tmp_path, capsys, _check_request(store))

    assert (code, out) == (2, "")
    assert err.startswith("close refused: ")
