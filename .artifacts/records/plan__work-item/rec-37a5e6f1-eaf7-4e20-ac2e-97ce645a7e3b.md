---
{
  "id": "rec-37a5e6f1-eaf7-4e20-ac2e-97ce645a7e3b",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "inline",
    "decisions": [
      "tiered-verification-scope",
      "tier2-execution"
    ],
    "effort": "workflow-loop",
    "estimate_minutes": 15,
    "executor": "inline",
    "kind": "deliver",
    "phase": "tiered-verification",
    "requirements": [
      "R5"
    ],
    "size": "S",
    "title": "Fix tier-2 failure in test_evidence_loop"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-10-11T10:13:13+00:00",
  "relationships": {},
  "revision": "sha256:f95b735e721ef34b1b190db7ea9a2e506b530f9be1b2525f56ccf46704f74f49",
  "subject": "fix-test_evidence_loop"
}
---

## Description

Tier-2 suite failure. Fix so the README full suite passes at phase head.

## Approach

Reproduce: `uv run --with pytest python -m pytest tests/test_evidence_loop.py -q -k check_run_result_and_method_are_contract_enums`
Failures: test_check_run_result_and_method_are_contract_enums
Fix tests and/or code on phase/tiered-verification; gitignore `.tier2/` if still missing.
