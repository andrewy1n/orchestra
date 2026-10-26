---
{
  "id": "rec-35ee1b24-285d-4f6e-a0ab-32ac1a4f52bc",
  "lifecycle_state": "superseded",
  "payload": {
    "confidence": "high",
    "effort": "workflow-loop",
    "missing": "",
    "next": "release",
    "phase": "task-worktrees",
    "requirement": "R6",
    "status": "verified"
  },
  "record_type": "run:assessment",
  "recorded_at": "2026-10-21T05:33:48+00:00",
  "relationships": {},
  "revision": "sha256:de4ae84e1829516c8a2a6d50359bad358c0132f1533ade0e949030d57ac78efc",
  "subject": "task-worktrees-R6",
  "time": {
    "as_of": "2026-10-21T05:28:52+00:00"
  }
}
---

## Evidence

Red check-run rec-21f49a84-bc5f-4d15-ad1d-8aca034752a4 result=fail revision=dirty runner=aff failed at assertion level on the frozen test. Green check-run rec-16902069-68a6-4350-b6fc-e442bcb4c64f result=pass revision=55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8. Oracle file hashes at that revision match the frozen oracle_hashes.

## Missing

none

## Reason

The task commit satisfies R6. The same frozen test failed before the edit and passed at the task commit.
