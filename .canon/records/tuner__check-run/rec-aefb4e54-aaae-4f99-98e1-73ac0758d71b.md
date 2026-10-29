---
{
  "id": "rec-aefb4e54-aaae-4f99-98e1-73ac0758d71b",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-6086fe65-7578-495f-9d43-2b6bef5009b8",
    "duration_s": 0.619724,
    "effort": "package-layout",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_shared_helpers.py::test_r20_views_calls_payload"
    ],
    "informed_by": [
      "rec-6086fe65-7578-495f-9d43-2b6bef5009b8"
    ],
    "method": "tdd",
    "output_sha256": "397712f0b91ce7f4aa868d961897b8ea6ae45e07a5be20763e61139a83b7f54b",
    "requirement": "R20",
    "result": "fail",
    "revision": "ca77219de4cb393d3b91d0a1a6f173160c784ec3",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-28T09:35:44+00:00",
  "relationships": {},
  "revision": "sha256:af65c700c607f4ca5b47d20784578688fcc61905dc785ea850ba11af9ca98c5c",
  "subject": "canon-record-payload-views"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_________________________ test_r20_views_calls_payload _________________________

    def test_r20_views_calls_payload() -> None:
        """R20: orchestra.views calls that function."""
        getters = _canon_record_payload_getters()
>       assert len(getters) == 1
E       assert 0 == 1
E        +  where 0 = len([])

tests/test_shared_helpers.py:622: AssertionError
=========================== short test summary info ============================
FAILED tests/test_shared_helpers.py::test_r20_views_calls_payload - assert 0 ...
1 failed in 0.10s
