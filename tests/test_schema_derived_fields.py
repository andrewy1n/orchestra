from __future__ import annotations

from collections.abc import Callable
from subprocess import CompletedProcess

import helpers as h
import pytest

Cli = Callable[..., CompletedProcess[str]]


@pytest.fixture()
def defs() -> dict[str, dict]:
    return h.schema_defs()


def _record(cli: Cli, defs: dict[str, dict], record_type: str, **payload: str) -> dict:
    return h.create_generic_record(cli, defs, record_type, extra_payload=payload)


def test_work_item_accepts_write_root(cli: Cli, defs: dict[str, dict]) -> None:
    item = _record(cli, defs, "score:work-item", write_root="/tmp/wt")
    assert item["payload"]["write_root"] == "/tmp/wt"
    assert "write_root" not in defs["score:work-item"]["required"]


def test_execution_report_without_assignment(cli: Cli, defs: dict[str, dict]) -> None:
    assert "assignment" not in defs["conductor:execution-report"]["required"]
    report = h.create_generic_record(cli, defs, "conductor:execution-report")
    assert "assignment" not in report["payload"]
    assert report["payload"]["work_item"]


def test_amendment_keyed_to_work_item(cli: Cli, defs: dict[str, dict]) -> None:
    item = h.create_generic_record(cli, defs, "score:work-item")
    amendment = _record(cli, defs, "conductor:assignment-amendment", work_item=item["id"])
    assert amendment["payload"]["work_item"] == item["id"]
    assert "assignment" not in amendment["payload"]


def test_old_assignment_linked_report_still_valid(cli: Cli, defs: dict[str, dict]) -> None:
    assignment = h.create_generic_record(cli, defs, "conductor:assignment")
    report = _record(
        cli,
        defs,
        "conductor:execution-report",
        work_item=assignment["payload"]["work_item"],
        assignment=assignment["id"],
    )
    assert report["payload"]["assignment"] == assignment["id"]
    old_amendment = _record(
        cli, defs, "conductor:assignment-amendment", assignment=assignment["id"]
    )
    assert old_amendment["payload"]["assignment"] == assignment["id"]
