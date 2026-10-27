"""Assertion-level oracle red classifier (R2)."""

from __future__ import annotations

import json

from affidavit.oracle_red import is_assertion_level_failure, is_assertion_level_red

# Realistic pytest tails (fixture shapes pinned by design).

ASSERTION_FAIL_TAIL = """\
============================= test session starts ==============================
collected 1 item

tests/test_oracle_probe.py::test_expected_behavior FAILED                 [100%]

_________________________ test_expected_behavior __________________________

    def test_expected_behavior():
>       assert compute() == 42
E       AssertionError: assert 0 == 42
E        +  where 0 = compute()

tests/test_oracle_probe.py:12: AssertionError
=========================== short test summary info ============================
FAILED tests/test_oracle_probe.py::test_expected_behavior - AssertionError: assert 0 == 42
============================== 1 failed in 0.02s ===============================
"""

IMPORT_FAIL_TAIL = """\
============================= test session starts ==============================
collected 0 items / 1 error

_________________ ERROR collecting tests/test_oracle_probe.py __________________
ImportError while importing test module '/tmp/tests/test_oracle_probe.py'.
tests/test_oracle_probe.py:1: in <module>
    from missing_pkg import compute
E   ModuleNotFoundError: No module named 'missing_pkg'
=========================== short test summary info ============================
ERROR tests/test_oracle_probe.py - ModuleNotFoundError: No module named 'missing_pkg'
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.05s ===============================
"""

COLLECTION_ERROR_TAIL = """\
============================= test session starts ==============================
collected 0 items / 1 error

_________________ ERROR collecting tests/test_broken.py __________________
tests/test_broken.py:3: in <module>
    class Bad:
E     SyntaxError: invalid syntax
=========================== short test summary info ============================
ERROR tests/test_broken.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.01s ===============================
"""

IMPORT_DURING_TEST_TAIL = """\
============================= test session starts ==============================
collected 1 item

tests/test_oracle_probe.py::test_import_inside FAILED                     [100%]

____________________________ test_import_inside ____________________________

    def test_import_inside():
>       import totally_missing_module
E       ModuleNotFoundError: No module named 'totally_missing_module'

tests/test_oracle_probe.py:4: ModuleNotFoundError
=========================== short test summary info ============================
FAILED tests/test_oracle_probe.py::test_import_inside - ModuleNotFoundError: No module named 'totally_missing_module'
============================== 1 failed in 0.02s ===============================
"""

NODE_ASSERT = "tests/test_oracle_probe.py::test_expected_behavior"
NODE_IMPORT_COLLECT = "tests/test_oracle_probe.py"
NODE_BROKEN = "tests/test_broken.py"
NODE_IMPORT_TEST = "tests/test_oracle_probe.py::test_import_inside"


def test_assertion_level_failure_true_for_assert_tail():
    assert is_assertion_level_failure(ASSERTION_FAIL_TAIL, [NODE_ASSERT]) is True


def test_assertion_level_failure_false_for_import_collection():
    assert is_assertion_level_failure(IMPORT_FAIL_TAIL, [NODE_IMPORT_COLLECT]) is False


def test_assertion_level_failure_false_for_collection_syntax_error():
    assert is_assertion_level_failure(COLLECTION_ERROR_TAIL, [NODE_BROKEN]) is False


def test_assertion_level_failure_false_for_import_error_during_test():
    assert is_assertion_level_failure(IMPORT_DURING_TEST_TAIL, [NODE_IMPORT_TEST]) is False


def test_assertion_level_failure_false_without_failing_nodes():
    assert is_assertion_level_failure(ASSERTION_FAIL_TAIL, []) is False


def test_is_assertion_level_red_true_for_fail_with_assert_body():
    check_run = {
        "body": ASSERTION_FAIL_TAIL,
        "payload": {
            "result": "fail",
            "failing_node_ids": json.dumps([NODE_ASSERT]),
        },
    }
    assert is_assertion_level_red(check_run) is True


def test_is_assertion_level_red_false_for_import_only():
    check_run = {
        "body": IMPORT_FAIL_TAIL,
        "payload": {
            "result": "fail",
            "failing_node_ids": json.dumps([NODE_IMPORT_COLLECT]),
        },
    }
    assert is_assertion_level_red(check_run) is False


def test_is_assertion_level_red_false_when_result_not_fail():
    check_run = {
        "body": ASSERTION_FAIL_TAIL,
        "payload": {
            "result": "pass",
            "failing_node_ids": json.dumps([NODE_ASSERT]),
        },
    }
    assert is_assertion_level_red(check_run) is False


def test_is_assertion_level_red_false_without_failing_node_ids():
    check_run = {
        "body": ASSERTION_FAIL_TAIL,
        "payload": {"result": "fail"},
    }
    assert is_assertion_level_red(check_run) is False


def test_oracle_red_accepts_flat_check_run_mapping():
    """Payload-shaped mapping (no nested payload) still classifies."""
    flat = {
        "result": "fail",
        "failing_node_ids": json.dumps([NODE_ASSERT]),
        "body": ASSERTION_FAIL_TAIL,
    }
    assert is_assertion_level_red(flat) is True
