---
{
  "id": "rec-40c358e7-d3bb-4dd6-9f3c-e72df9effce7",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "dashboard",
    "missing": "",
    "next": "release",
    "phase": "deep-links",
    "requirement": "R4",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-20T04:39:41+00:00",
  "relationships": {},
  "revision": "sha256:837ac569a3dd1ee30d998b3f3ea981176a79e67576baec3f44260fbd919dd890",
  "subject": "deep-links-R4",
  "time": {
    "as_of": "2026-10-20T04:39:41+00:00"
  }
}
---

## Evidence

check-run rec-9e27f631-06b0-4612-848f-457c7f2e0611 pass at 3216e017 (vitest links.test.ts -t R4)

## Missing

none

## Reason

The resolve helper satisfies R4 at the cited revision; the focused check passed.
