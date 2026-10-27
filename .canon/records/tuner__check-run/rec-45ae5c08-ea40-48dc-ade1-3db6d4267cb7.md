---
{
  "id": "rec-45ae5c08-ea40-48dc-ade1-3db6d4267cb7",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-3a9261a1-b666-48fc-a9b4-068838f86307",
    "diff_sha256": "de15c65ea221493911e47157ac1aa5f1d6450b1d1ee42273598be78b77f57e60",
    "duration_s": 0.730947,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_tiered_verification.py::test_suite_record_writes_runner_orchestra"
    ],
    "informed_by": [
      "rec-3a9261a1-b666-48fc-a9b4-068838f86307",
      "rec-06c2c453-77a0-4f70-8f8a-17ee4023cef5"
    ],
    "method": "tdd",
    "output_sha256": "5f6116bd664a66141f74eb39478d44380bdcd32f62b5a596816888bf07364bb9",
    "requirement": "R2",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "honest-runner-stamp-suite"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-21T06:51:56+00:00",
  "relationships": {},
  "revision": "sha256:34b17301b23605f0cf4f32824f2ac19f9b1ef90a0410cd42c4d967849b1b07d6",
  "subject": "honest-runner-stamp-suite",
  "time": {
    "observed": "2026-10-21T06:51:56+00:00",
    "recorded": "2026-10-21T06:51:56+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
__________________ test_suite_record_writes_runner_orchestra ___________________

    def test_suite_record_writes_runner_orchestra():
        """R2: suite check-run writer stamps payload.runner as orchestra."""
>       assert False, "forced dirty red"
E       AssertionError: forced dirty red
E       assert False

tests/test_tiered_verification.py:171: AssertionError
=========================== short test summary info ============================
FAILED tests/test_tiered_verification.py::test_suite_record_writes_runner_orchestra
1 failed in 0.12s
