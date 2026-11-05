from __future__ import annotations

import subprocess
from pathlib import Path

from canon_support import create, make_project

from orchestra.conductor.check import parse_failing_node_ids, run_check

SPACED = "tests/test_effort_brief.py::test_r3_sections[Success measure]"
DASHED = "tests/test_a.py::test_x[left - right]"


def test_parse_keeps_a_spaced_parameter_id_whole() -> None:
    output = f"FAILED {SPACED} - AssertionError: nope\n"
    assert parse_failing_node_ids(output) == [SPACED]


def test_parse_keeps_a_spaced_parameter_id_whole_without_a_message() -> None:
    assert parse_failing_node_ids(f"FAILED {SPACED}\n") == [SPACED]


def test_parse_keeps_a_parameter_that_contains_the_message_separator() -> None:
    output = f"FAILED {DASHED} - AssertionError: nope\n"
    assert parse_failing_node_ids(output) == [DASHED]


def test_parse_reads_an_error_line_with_a_spaced_id() -> None:
    assert parse_failing_node_ids(f"ERROR {SPACED} - RuntimeError\n") == [SPACED]


def test_parse_still_reads_unspaced_ids_in_order_without_duplicates() -> None:
    output = (
        "FAILED tests/test_a.py::test_one - AssertionError\n"
        "FAILED tests/test_b.py::TestCls::test_two - AssertionError\n"
        "FAILED tests/test_a.py::test_one\n"
    )
    assert parse_failing_node_ids(output) == [
        "tests/test_a.py::test_one",
        "tests/test_b.py::TestCls::test_two",
    ]


def test_check_run_stores_the_whole_spaced_node_id(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@example.com",
            "commit",
            "--allow-empty",
            "-qm",
            "base",
        ],
        check=True,
    )
    create(project, "score:effort", "ef", {"goal": "g", "kind": "deliver"})
    acceptance = create(
        project,
        "score:acceptance",
        "spaced",
        {
            "method": "check",
            "phase": "",
            "effort": "ef",
            "verify_command": f"printf 'FAILED {SPACED} - AssertionError\\n'; exit 1",
        },
    )
    outcome = run_check(
        acceptance_id=acceptance["id"], cwd=tmp_path, store_root=tmp_path, allow_dirty=True
    )
    assert outcome.exit_code == 1
    assert outcome.record is not None
    assert outcome.record["payload"]["failing_node_ids"] == [SPACED]
