---
{
  "id": "rec-4dc59d6d-f6b1-42ef-bdec-b1329a36a8b2",
  "lifecycle_state": "superseded",
  "payload": {
    "confidence": "low",
    "effort": "dashboard",
    "level": "verification",
    "missing": "acceptance",
    "next": "verify",
    "phase": "estimate-view",
    "requirement": "R4",
    "status": "insufficient"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-05T07:20:22+00:00",
  "relationships": {},
  "revision": "sha256:61a90a16483f49acea91232ddf3d48438fedf0d5e12c35537d2395a96e8dbd5f",
  "subject": "estimate-view-R4",
  "time": {
    "as_of": "2026-10-05T07:00:40+00:00"
  }
}
---

## Evidence

test_estimate_view_row_fields failed before the model change and then passed. A task row carries size, estimate_minutes, and executor from the work-item.

## Missing

acceptance

## Reason

The unit check passed. The task-title suffix pilot for R4 has not run.
