---
{
  "id": "rec-feec2528-93aa-43db-acca-838420bfa2e2",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "dashboard",
    "missing": "",
    "next": "release",
    "phase": "area-levels",
    "requirement": "R3",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-30T08:27:29+00:00",
  "relationships": {},
  "revision": "sha256:aec70ad977da839cbd8a5359ceabedbb1a0a04d8a9eb2615ad2a68f946a2ef47",
  "subject": "area-levels-R3"
}
---

## Evidence

- product-index-r3 (R3, tdd): green check-run rec-6ddb4a3a-ea1d-40e3-9417-056d1b232c08 at 3384242e730e

## Missing

none

## Reason

Every check this task runs for R3 passed. For oracle-backed acceptances the assertion-level red, the green at a descendant revision, and the frozen hashes all hold. The phase verification task re-checks R3 later.
