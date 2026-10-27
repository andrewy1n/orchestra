---
{
  "id": "rec-7f20d856-7d9c-4e47-8f58-3f3afebe34b0",
  "lifecycle_state": "planned",
  "payload": {
    "assignee": "",
    "decisions": [
      "audit-hunk-mutants",
      "audit-interface"
    ],
    "depends_on": [
      "audit-blocks",
      "audit-mutants"
    ],
    "effort": "evidence-layer",
    "estimate_minutes": 8,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "phase-end-evidence",
    "requirements": [
      "R1",
      "R2",
      "R3",
      "R4"
    ],
    "size": "M",
    "title": "Verify phase-end evidence"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-18T04:13:06+00:00",
  "relationships": {},
  "revision": "sha256:79401dfeada7d121a0fafe11bf67b1ea79a5befaa4ee56df560c78e0ab6b87aa",
  "subject": "verify-phase-end-evidence"
}
---

## Description

Prove the phase exit criteria hold together: run every acceptance verify_command through the real `bin/aff` entry point and return the results.

## Approach

Run each verify_command from the acceptances only. Do not edit the tree; if a check fails return `fail` with the output.
