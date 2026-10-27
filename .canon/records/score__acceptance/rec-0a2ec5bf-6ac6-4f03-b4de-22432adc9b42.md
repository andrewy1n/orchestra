---
{
  "id": "rec-0a2ec5bf-6ac6-4f03-b4de-22432adc9b42",
  "lifecycle_state": "active",
  "payload": {
    "effort": "library-boundary",
    "method": "check",
    "phase": "claim-clocks",
    "requirement": "R1,R5,R6,R8",
    "verify_command": "python3 -m pytest tests/test_claim_clocks.py tests/test_close_batch.py tests/test_orchestra_callers.py \"tests/test_verify_authority.py::test_close_batch_still_creates_manual_check_runs\" -q"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-23T09:32:22+00:00",
  "relationships": {},
  "revision": "sha256:7a0b3bfea83045f59f27857436dbb5dcc50a8b6eee753230e0217944daca04f8",
  "subject": "fix-claim-gate-regressions",
  "time": {
    "as_of": "2026-10-23T09:32:22+00:00"
  }
}
---

