---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-7a05df17-bd22-4db2-a3e9-eaf3b764fe5e",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "real_gap check-path survivors from spikes/llm-mutants/findings.md are killed: timeout as blocked, empty verify_command refused, CLI --cwd forwarded (plus any check store-cwd gap not already covered by R5)",
    "effort": "workflow-loop",
    "method": "tdd",
    "phase": "claim-witnesses",
    "requirement": "R6",
    "verify_command": "python3 -m pytest tests/test_affidavit_check.py -k 'timeout or empty_verify or cwd_forwarded or blocked_timeout' -q"
  },
  "record_type": "project:acceptance",
  "recorded_at": "2026-10-16T09:29:09+00:00",
  "relationships": {},
  "revision": "sha256:729f8af93dc734cbcb59508253f4ea98b0e7199875cdffa812060bc749983b58",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "verify-path-test-gaps-mutants",
  "time": {
    "as_of": "2026-10-16T09:29:09+00:00"
  }
}
---

