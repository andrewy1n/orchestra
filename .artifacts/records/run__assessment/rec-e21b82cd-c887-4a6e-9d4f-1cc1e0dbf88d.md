---
{
  "id": "rec-e21b82cd-c887-4a6e-9d4f-1cc1e0dbf88d",
  "lifecycle_state": "superseded",
  "payload": {
    "confidence": "high",
    "effort": "workflow-loop",
    "missing": "",
    "next": "release",
    "phase": "task-worktrees",
    "requirement": "R14",
    "status": "verified"
  },
  "record_type": "run:assessment",
  "recorded_at": "2026-10-21T05:33:57+00:00",
  "relationships": {},
  "revision": "sha256:becfcc4a7c23948b9aae5b450a67dfc614d56402a0b2e2467c0e261096ee3981",
  "subject": "task-worktrees-R14",
  "time": {
    "as_of": "2026-10-21T05:29:01+00:00"
  }
}
---

## Evidence

Red check-run rec-cfa110cb-1402-4b7b-af1c-806428cf8b81 result=fail revision=dirty runner=aff failed at assertion level on the frozen test. Green check-run rec-a0ca9c78-e1f3-42c2-a266-8e57ded83242 result=pass revision=55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8. Oracle file hashes at that revision match the frozen oracle_hashes.

## Missing

none

## Reason

The task commit satisfies R14. The same frozen test failed before the edit and passed at the task commit.
