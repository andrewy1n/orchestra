---
{
  "id": "rec-6feee6e6-c6b7-49fe-ae99-df5af171b595",
  "lifecycle_state": "superseded",
  "payload": {
    "confidence": "high",
    "effort": "workflow-loop",
    "missing": "",
    "next": "release",
    "phase": "task-worktrees",
    "requirement": "R10",
    "status": "verified"
  },
  "record_type": "run:assessment",
  "recorded_at": "2026-10-21T05:34:05+00:00",
  "relationships": {},
  "revision": "sha256:c14b9b3b9765a69eb69515e6c15351ccc67a9fa09ed83f5c35d8f11f8151dc01",
  "subject": "task-worktrees-R10",
  "time": {
    "as_of": "2026-10-21T05:29:07+00:00"
  }
}
---

## Evidence

Red check-run rec-db22c554-37b8-47e3-8914-647f46759ef9 result=fail revision=dirty runner=aff failed at assertion level on the frozen test. Green check-run rec-21bb8566-0502-4a09-97e1-850716895aa6 result=pass revision=55e29a6c1dc3ad08bbe3d6af777bbb09bda0aba8. Oracle file hashes at that revision match the frozen oracle_hashes.

## Missing

none

## Reason

The task commit satisfies R10. The same frozen test failed before the edit and passed at the task commit.
