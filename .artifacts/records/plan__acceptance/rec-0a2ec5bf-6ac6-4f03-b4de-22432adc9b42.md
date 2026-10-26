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
  "record_type": "plan:acceptance",
  "recorded_at": "2026-10-23T09:32:22+00:00",
  "relationships": {},
  "revision": "sha256:f26753c5be2c9e08f58bfbe21a32bc0ea888fff237dfbb76f1d7b574c55fb41a",
  "subject": "fix-claim-gate-regressions",
  "time": {
    "as_of": "2026-10-23T09:32:22+00:00"
  }
}
---

