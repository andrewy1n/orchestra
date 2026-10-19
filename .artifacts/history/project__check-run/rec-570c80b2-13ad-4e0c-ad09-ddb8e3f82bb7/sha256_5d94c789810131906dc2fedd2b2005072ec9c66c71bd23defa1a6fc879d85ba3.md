---
{
  "base_kind": "event",
  "id": "rec-570c80b2-13ad-4e0c-ad09-ddb8e3f82bb7",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-15f765d5-4785-4b60-8e28-1e0c176acff4",
    "diff_sha256": "fe70fae1529348c11d273267086c13125befe22efe531081c56f7cdb015dd628",
    "duration_s": 0.266841,
    "effort": "packaging",
    "exit_code": 1,
    "method": "tdd",
    "output_sha256": "01d29aa421b4d2de8862c1e7a7008522e422b4f43aaf5bec99f26202e3fa607c",
    "requirement": "R2",
    "result": "fail",
    "revision": "dirty",
    "runner": "se-workflow",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "shared-aa-resolver"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-14T08:35:38+00:00",
  "relationships": {
    "informed_by": [
      "rec-15f765d5-4785-4b60-8e28-1e0c176acff4",
      "rec-7234a189-d1f2-4e59-b372-70173925f6e5"
    ]
  },
  "revision": "sha256:5d94c789810131906dc2fedd2b2005072ec9c66c71bd23defa1a6fc879d85ba3",
  "subject": "shared-aa-resolver",
  "time": {
    "observed": "2026-10-14T08:35:38+00:00",
    "recorded": "2026-10-14T08:35:38+00:00"
  }
}
---

......F                                                                  [100%]
=================================== FAILURES ===================================
________________________________ test_force_red ________________________________

>   def test_force_red(): assert False
                          ^^^^^^^^^^^^
E   assert False

tests/test_aa_resolve.py:114: AssertionError
=========================== short test summary info ============================
FAILED tests/test_aa_resolve.py::test_force_red - assert False
1 failed, 6 passed in 0.06s
