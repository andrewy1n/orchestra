---
{
  "id": "rec-7a05df17-bd22-4db2-a3e9-eaf3b764fe5e",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "real_gap check-path survivors from spikes/llm-mutants/findings.md are killed: timeout as blocked, empty verify_command refused, CLI --cwd forwarded (plus any check store-cwd gap not already covered by R5)",
    "effort": "workflow-loop",
    "method": "tdd",
    "phase": "claim-witnesses",
    "requirement": "R6",
    "verify_command": "python3 -m pytest tests/test_affidavit_check.py -k 'timeout or empty_verify or cwd_forwarded or blocked_timeout' -q"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-16T09:29:09+00:00",
  "relationships": {},
  "revision": "sha256:798bd5956fbf82539e3034d3e6b43067a0e485e0edc0f32a545fa1f651bd5adf",
  "subject": "verify-path-test-gaps-mutants",
  "time": {
    "as_of": "2026-10-16T09:29:09+00:00"
  }
}
---

