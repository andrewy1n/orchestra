---
{
  "id": "rec-e2aeedd4-e2ff-48c7-9eda-cb69477252ce",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "verify-affidavit-library-agent",
    "decisions": [
      "affidavit-store-client",
      "dependency-direction",
      "call-style",
      "three-repos"
    ],
    "depends_on": [
      "store-client",
      "verdict-gate"
    ],
    "effort": "library-boundary",
    "estimate_minutes": 8,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "affidavit-library",
    "requirements": [
      "R5",
      "R7",
      "R9",
      "R10"
    ],
    "size": "S",
    "title": "Verify affidavit calls Project and verdict stays store-free"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-21T10:24:29+00:00",
  "relationships": {},
  "revision": "sha256:e2a50e354335f6e618c0c2cbba85ddfe33227d624c0cd1b87d5d2c0f5a0159fc",
  "subject": "verify-affidavit-library"
}
---

## Description

Prove the phase exit criteria hold together: observation and binding go through `Project`, no affidavit module starts `adaptive-artifacts`, `aff --help` still lists verdict, recheck, and assertion-red, and `run_verdict` does not need a store.

R5: No module under `affidavit/` starts a process to run `adaptive-artifacts`.
R7: `aff assertion-red` exits 0 when `is_assertion_level_red` is true.
R9: `aff verdict` calls `run_verdict` without opening an artifact store to decide the gate.
R10: `run_verdict` returns a verdict for a repository that has no artifact store.

## Approach

Run the integration checks through `aff` and the affidavit tests. Do not edit the tree. Return fail if any check fails.
