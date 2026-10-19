---
{
  "base_kind": "event",
  "id": "rec-3e568900-d5ec-445c-9d0c-ba14ccaeae3f",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-e094b9fe-4161-4ebd-81ad-00b66dce7444",
    "diff_sha256": "dbe4d631378668406bc8bdc21c4f8c21b61333eacc665955a80a9e87b20a5b45",
    "duration_s": 0.297341,
    "effort": "workflow-loop",
    "exit_code": 2,
    "method": "tdd",
    "output_sha256": "69ca689ba91a279a5af8b8c0922107d4801e9a8a0d53dab54c0a4cb5ec920dbe",
    "requirement": "R2",
    "result": "fail",
    "revision": "dirty",
    "runner": "se-workflow",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "verify-tiered-verification"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-11T09:44:09+00:00",
  "relationships": {
    "informed_by": [
      "rec-e094b9fe-4161-4ebd-81ad-00b66dce7444",
      "rec-01506d98-f3b3-41af-b410-b9eaf9196043"
    ]
  },
  "revision": "sha256:31731fcdc7fb8f1114c331d07f4ac0ae6fb2436d31142afa827550203209892b",
  "subject": "verify-tiered-verification",
  "time": {
    "observed": "2026-10-11T09:44:09+00:00",
    "recorded": "2026-10-11T09:44:09+00:00"
  }
}
---

==================================== ERRORS ====================================
______________ ERROR collecting tests/test_tiered_verification.py ______________
tests/test_tiered_verification.py:418: in <module>
    assert False, "intentional red"
E   AssertionError: intentional red
E   assert False
=========================== short test summary info ============================
ERROR tests/test_tiered_verification.py - AssertionError: intentional red
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.11s
