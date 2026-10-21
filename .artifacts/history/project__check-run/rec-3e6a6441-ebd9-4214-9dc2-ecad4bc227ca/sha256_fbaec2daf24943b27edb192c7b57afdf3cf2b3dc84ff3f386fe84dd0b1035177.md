---
{
  "base_kind": "event",
  "id": "rec-3e6a6441-ebd9-4214-9dc2-ecad4bc227ca",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-ef0fb7b2-c352-4dab-92c7-eaab8da90860",
    "diff_sha256": "9a1fb60bb4314996776a5b5a9f1939e986fd643cc885b5c3559a4acc96d8dae3",
    "duration_s": 0.786405,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": "[\"tests/test_close_batch.py::test_close_batch_accepts_orchestra_runner_stamp\"]",
    "method": "tdd",
    "output_sha256": "ecb37f4c6269f6effed2ebf5463c5374e271af71eda606e9225b76904a171963",
    "requirement": "R3",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "honest-runner-stamp-accept"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-21T06:51:57+00:00",
  "relationships": {
    "informed_by": [
      "rec-ef0fb7b2-c352-4dab-92c7-eaab8da90860",
      "rec-06c2c453-77a0-4f70-8f8a-17ee4023cef5"
    ]
  },
  "revision": "sha256:fbaec2daf24943b27edb192c7b57afdf3cf2b3dc84ff3f386fe84dd0b1035177",
  "subject": "honest-runner-stamp-accept",
  "time": {
    "observed": "2026-10-21T06:51:57+00:00",
    "recorded": "2026-10-21T06:51:57+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_______________ test_close_batch_accepts_orchestra_runner_stamp ________________

    def test_close_batch_accepts_orchestra_runner_stamp():
        """R3: stored check-run is runner-produced only when runner is orchestra."""
>       assert False, "forced dirty red"
E       AssertionError: forced dirty red
E       assert False

tests/test_close_batch.py:1559: AssertionError
=========================== short test summary info ============================
FAILED tests/test_close_batch.py::test_close_batch_accepts_orchestra_runner_stamp
1 failed in 0.15s
