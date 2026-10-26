---
{
  "id": "rec-ee6da65a-abd9-44fa-84f6-3d55a6e38ae2",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-3e1157f5-8e67-4d05-9433-8ddc7f9e38f3",
    "diff_sha256": "81530aa10ba8e790dbfba8d2fb5d5053c9afc8b03a0ee33618db2880e6cde420",
    "duration_s": 0.729894,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_close_batch.py::test_close_batch_refuses_aff_runner_stamp"
    ],
    "informed_by": [
      "rec-3e1157f5-8e67-4d05-9433-8ddc7f9e38f3"
    ],
    "method": "tdd",
    "output_sha256": "360302af0c5e46808d9c5764ef73ca976cd0045c635b65671611dfabb934f0be",
    "requirement": "R4",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "honest-runner-stamp-refuse-aff"
    ]
  },
  "record_type": "aff:check-run",
  "recorded_at": "2026-10-21T06:34:19+00:00",
  "relationships": {},
  "revision": "sha256:7579ee02f328237c39a51c914dfbc6de26ec47286525e5445a756c21db2ce95a",
  "subject": "honest-runner-stamp-refuse-aff",
  "time": {
    "observed": "2026-10-21T06:34:19+00:00",
    "recorded": "2026-10-21T06:34:19+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
__________________ test_close_batch_refuses_aff_runner_stamp ___________________

    def test_close_batch_refuses_aff_runner_stamp():
        """R4: stored check-run with runner aff is not runner-produced."""
        request = _request(
            criteria=[
                {
                    "criterion_id": "rec-ac1",
                    "method": "check",
                    "check_run_id": "rec-runner-cr",
                    "result": "pass",
                    "runner": "aff",
                }
            ]
        )
>       with pytest.raises(close_batch.CloseRefused) as excinfo:
E       Failed: DID NOT RAISE <class 'orchestra.close_batch.CloseRefused'>

tests/test_close_batch.py:1594: Failed
=========================== short test summary info ============================
FAILED tests/test_close_batch.py::test_close_batch_refuses_aff_runner_stamp
1 failed in 0.12s
