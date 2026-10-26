---
{
  "id": "rec-71acb210-c402-465e-9c0b-3fbcdbcf4b46",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-b8ca9700-c0a5-4278-be0f-c17529d6acd5",
    "diff_sha256": "d465390281606a15ca4bbf5bc797318e818f5048dbe95fd789b919104d80979e",
    "duration_s": 0.605418,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_affidavit_import_boundary.py::test_close_batch_does_not_import_affidavit"
    ],
    "informed_by": [
      "rec-b8ca9700-c0a5-4278-be0f-c17529d6acd5",
      "rec-ec62c47e-092d-4eb9-b67d-2f87e1e27925"
    ],
    "method": "tdd",
    "output_sha256": "5118c689a606e10dfebd174a542105b27583d0014f3aefbf60f5e392b9671ecb",
    "requirement": "R8",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "oracle-red-cli-surface"
    ]
  },
  "record_type": "aff:check-run",
  "recorded_at": "2026-10-21T06:53:26+00:00",
  "relationships": {},
  "revision": "sha256:fc088519fde4b10453519164eeaafbbe26c48826ff60b18540ce1a9166ade84b",
  "subject": "oracle-red-cli-surface",
  "time": {
    "observed": "2026-10-21T06:53:26+00:00",
    "recorded": "2026-10-21T06:53:26+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
__________________ test_close_batch_does_not_import_affidavit __________________

    def test_close_batch_does_not_import_affidavit():
        """R8: orchestra close-batch must not import the affidavit package."""
>       assert False, "forced dirty red"
E       AssertionError: forced dirty red
E       assert False

tests/test_affidavit_import_boundary.py:47: AssertionError
=========================== short test summary info ============================
FAILED tests/test_affidavit_import_boundary.py::test_close_batch_does_not_import_affidavit
1 failed in 0.05s
