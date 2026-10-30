---
{
  "id": "rec-eacc5456-2fb4-4d69-bfc0-da883d24f0ac",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "dashboard",
    "missing": "",
    "next": "release",
    "phase": "area-levels",
    "requirement": "R6",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-30T08:27:33+00:00",
  "relationships": {},
  "revision": "sha256:5b1d4fb02acc75201d7b7cb74e5d41131f9bc0e0ca36007760a218d1aa2734d3",
  "subject": "area-levels-R6"
}
---

## Evidence

- product-index-r6 (R6, tdd): green check-run rec-4ac8fba6-07fe-48ad-9f0d-06f07406c870 at 3384242e730e

## Missing

none

## Reason

Every check this task runs for R6 passed. For oracle-backed acceptances the assertion-level red, the green at a descendant revision, and the frozen hashes all hold. The phase verification task re-checks R6 later.
