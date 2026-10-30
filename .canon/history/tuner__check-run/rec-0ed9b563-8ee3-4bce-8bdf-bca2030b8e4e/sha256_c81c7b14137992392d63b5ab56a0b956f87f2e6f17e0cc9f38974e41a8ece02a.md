---
{
  "id": "rec-0ed9b563-8ee3-4bce-8bdf-bca2030b8e4e",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-f9801171-1133-4a4a-ab26-6061ce12f790",
    "diff_sha256": "fd9d7734ac9e10abb19025f20ecd0ffc9dfadc3930054f8bc9274db2bef7453d",
    "duration_s": 0.26632,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_effort_brief.py::test_r5_module_version_is_1_1_0"
    ],
    "informed_by": [
      "rec-f9801171-1133-4a4a-ab26-6061ce12f790"
    ],
    "method": "tdd",
    "output_sha256": "856349ba92f06c9f04c40ebc3510ccd4f5f5b0d0ef5c01c93a7a0c8fc1060048",
    "requirement": "R5",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T17:07:38+00:00",
  "relationships": {},
  "revision": "sha256:c81c7b14137992392d63b5ab56a0b956f87f2e6f17e0cc9f38974e41a8ece02a",
  "subject": "brief-schema-r5"
}
---

F                                                                                                                                                                                                                                                  [100%]
======================================================================================================================== FAILURES ========================================================================================================================
____________________________________________________________________________________________________________ test_r5_module_version_is_1_1_0 _____________________________________________________________________________________________________________

    def test_r5_module_version_is_1_1_0():
>       assert _module()["version"] == "1.1.0"
E       AssertionError: assert '1.0.0' == '1.1.0'
E
E         - 1.1.0
E         + 1.0.0

tests/test_effort_brief.py:123: AssertionError
================================================================================================================ short test summary info =================================================================================================================
FAILED tests/test_effort_brief.py::test_r5_module_version_is_1_1_0 - AssertionError: assert '1.0.0' == '1.1.0'
1 failed, 10 deselected in 0.04s
