---
{
  "id": "rec-ca2bbe1f-452e-4d84-9a5b-54f8ff3fd87c",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "dashboard",
    "missing": "",
    "next": "release",
    "phase": "area-levels",
    "requirement": "R1",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-30T08:55:49+00:00",
  "relationships": {
    "supersedes": [
      "rec-49bb7e26-06d4-484d-b267-700bae44181d"
    ]
  },
  "revision": "sha256:66864345c4bd9b86fe686f05fea0de445fdcb695964710f05e05ffb65a5780c4",
  "subject": "area-levels-R1"
}
---

## Evidence

- fix-area-levels-levels-product (R1, tdd): green check-run rec-e2b9479c-34c7-42f9-880b-743cdda8b5f5 at 7e0a1192c2bf

## Missing

none

## Reason

Every check this task runs for R1 passed. For oracle-backed acceptances the assertion-level red, the green at a descendant revision, and the frozen hashes all hold. The phase verification task re-checks R1 later.
