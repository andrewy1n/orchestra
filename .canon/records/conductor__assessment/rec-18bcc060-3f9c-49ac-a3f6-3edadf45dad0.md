---
{
  "id": "rec-18bcc060-3f9c-49ac-a3f6-3edadf45dad0",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "dashboard",
    "missing": "",
    "next": "release",
    "phase": "effort-area-link",
    "requirement": "R1",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-30T07:31:17+00:00",
  "relationships": {
    "supersedes": [
      "rec-a02a1b93-f65a-45ba-8d36-b33b76c8a353"
    ]
  },
  "revision": "sha256:f9665d2eb46d01d038564ca9f5b7207a328a1973f5422e810b8d3b565021f97a",
  "subject": "effort-area-link-R1"
}
---

## Evidence

- verify-effort-area-link-schema (R1, check): green check-run rec-046f2321-2807-41ca-adf2-ff93668f0efc at 25a389b24ced

## Missing

none

## Reason

Every check this task runs for R1 passed. For oracle-backed acceptances the assertion-level red, the green at a descendant revision, and the frozen hashes all hold. The phase verification task re-checks R1 later.
