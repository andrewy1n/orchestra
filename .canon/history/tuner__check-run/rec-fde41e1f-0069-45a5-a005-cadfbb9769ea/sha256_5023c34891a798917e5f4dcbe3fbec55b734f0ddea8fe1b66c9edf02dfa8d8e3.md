---
{
  "id": "rec-fde41e1f-0069-45a5-a005-cadfbb9769ea",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-85630b31-3c07-4f31-9cd9-6c4b31419fc9",
    "duration_s": 0.588896,
    "effort": "evidence-layer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_orchestra_package.py::test_reviewer_and_suite_import"
    ],
    "informed_by": [
      "rec-85630b31-3c07-4f31-9cd9-6c4b31419fc9",
      "rec-7c205690-5dbf-4986-8912-d0f2684261e0"
    ],
    "method": "tdd",
    "output_sha256": "00cd70337c9ae4a19b26e303453bb6abf774970cf34f6fef3bbb974a334c20f1",
    "requirement": "R2",
    "result": "fail",
    "revision": "dcbe257640b906280cb8cdc8a72c531dc1c4cee0",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "scaffold-orchestra"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-17T07:54:05+00:00",
  "relationships": {},
  "revision": "sha256:5023c34891a798917e5f4dcbe3fbec55b734f0ddea8fe1b66c9edf02dfa8d8e3",
  "subject": "scaffold-orchestra",
  "time": {
    "observed": "2026-10-17T07:54:05+00:00",
    "recorded": "2026-10-17T07:54:05+00:00"
  }
}
---

F..                                                                      [100%]
=================================== FAILURES ===================================
________________________ test_reviewer_and_suite_import ________________________

    def test_reviewer_and_suite_import():
>       import orchestra.reviewer  # noqa: F401
E       ModuleNotFoundError: No module named 'orchestra'

tests/test_orchestra_package.py:11: ModuleNotFoundError
=========================== short test summary info ============================
FAILED tests/test_orchestra_package.py::test_reviewer_and_suite_import - Modu...
1 failed, 2 passed in 0.04s
