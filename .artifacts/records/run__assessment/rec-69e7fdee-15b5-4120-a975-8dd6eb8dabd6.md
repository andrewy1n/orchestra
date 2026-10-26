---
{
  "id": "rec-69e7fdee-15b5-4120-a975-8dd6eb8dabd6",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "dashboard",
    "missing": "",
    "next": "release",
    "phase": "human-gates",
    "requirement": "R6",
    "status": "verified"
  },
  "record_type": "run:assessment",
  "recorded_at": "2026-10-09T21:06:49+00:00",
  "relationships": {},
  "revision": "sha256:7bfc3e170dbff8dcde63262674188066df918f3b5107667157141c25b6b8f42e",
  "subject": "human-gates-R6",
  "time": {
    "as_of": "2026-10-09T21:06:49+00:00"
  }
}
---

## Evidence

Unit check-run gates-model for R6 passed (merge-branch Needs you after integration with branch/ahead).

## Missing

none

## Reason

merge_landing_needs produces Merge branch items for done unmerged Landing phases in the required order.
