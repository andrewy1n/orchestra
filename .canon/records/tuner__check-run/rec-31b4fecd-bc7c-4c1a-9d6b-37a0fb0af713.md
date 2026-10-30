---
{
  "id": "rec-31b4fecd-bc7c-4c1a-9d6b-37a0fb0af713",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-927f6e03-da07-4e46-8016-0bc1a3094b8b",
    "diff_sha256": "667da4bd9b933fa5241af238da767d368d846305cb5780537d534c78d44b1e25",
    "duration_s": 0.311254,
    "effort": "ci",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_ci_workflow.py::test_mypy_gate_r11_types_steps_do_not_continue_on_error"
    ],
    "informed_by": [
      "rec-927f6e03-da07-4e46-8016-0bc1a3094b8b"
    ],
    "method": "tdd",
    "output_sha256": "92904e29053f538e869e66148db781d89a5cf65e82299b625c499cdf64e7db95",
    "requirement": "R11",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T07:45:35+00:00",
  "relationships": {},
  "revision": "sha256:9d318a3ae2d6f0a766912798dba86fb94897568c2866d17de7fc6b8bf664ed33",
  "subject": "types-job-blocking-steps"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
___________ test_mypy_gate_r11_types_steps_do_not_continue_on_error ____________

    def test_mypy_gate_r11_types_steps_do_not_continue_on_error():
        steps = job("types").get("steps", [])
        checks = [step for step in steps if "basedpyright" in str(step.get("run", ""))]
>       assert checks, "types job has no basedpyright step"
E       AssertionError: types job has no basedpyright step
E       assert []

tests/test_ci_workflow.py:231: AssertionError
=========================== short test summary info ============================
FAILED tests/test_ci_workflow.py::test_mypy_gate_r11_types_steps_do_not_continue_on_error
1 failed, 24 deselected in 0.06s
