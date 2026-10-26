---
{
  "id": "rec-3c0efe4d-b221-4c3e-8a22-1ef4b5b4ab91",
  "lifecycle_state": "active",
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
  "relationships": {
    "supersedes": [
      "rec-e21b82cd-c887-4a6e-9d4f-1cc1e0dbf88d"
    ]
  },
  "revision": "sha256:19b43db1e0dbd8d9fbdd335c8bfcd5a016317c4764e8731ab6bca28f59728749",
  "subject": "task-worktrees-R14",
  "time": {
    "as_of": "2026-10-21T05:33:57+00:00"
  }
}
---

## Evidence

Red check-run rec-bccb9b5e-0260-4c2d-b946-e55f7fc81317 result=fail revision=dirty runner=aff failed at assertion level on the frozen test. Green check-run rec-a0ca9c78-e1f3-42c2-a266-8e57ded83242 result=pass revision=55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8. Oracle file hashes at that revision match the frozen oracle_hashes.

## Missing

none

## Reason

The task commit satisfies R14. The same frozen test failed before the edit and passed at the task commit.
