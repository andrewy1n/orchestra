---
{
  "id": "rec-a3bfed7e-d0bb-480f-9e11-100266b09aab",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-7508712a-f562-4444-a02e-2f68d2cc076d",
    "duration_s": 0.610371,
    "effort": "package-layout",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_shared_helpers.py::test_r21_close_batch_calls_payload"
    ],
    "informed_by": [
      "rec-7508712a-f562-4444-a02e-2f68d2cc076d"
    ],
    "method": "tdd",
    "output_sha256": "a45cc125244d0db709f23d7aa42e71286a77720d35a4c12bbdfba04da1606585",
    "requirement": "R21",
    "result": "fail",
    "revision": "ca77219de4cb393d3b91d0a1a6f173160c784ec3",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-28T09:35:47+00:00",
  "relationships": {},
  "revision": "sha256:a4205482547798088b6f93c807e68512004388b7269abcf407351c81d2f7d2dd",
  "subject": "canon-record-payload-batch"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
______________________ test_r21_close_batch_calls_payload ______________________

    def test_r21_close_batch_calls_payload() -> None:
        """R21: orchestra.conductor.close_batch calls that function."""
        getters = _canon_record_payload_getters()
>       assert len(getters) == 1
E       assert 0 == 1
E        +  where 0 = len([])

tests/test_shared_helpers.py:629: AssertionError
=========================== short test summary info ============================
FAILED tests/test_shared_helpers.py::test_r21_close_batch_calls_payload - ass...
1 failed in 0.10s
