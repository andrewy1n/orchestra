---
{
  "id": "rec-aa80746f-9af7-4fc5-aeb8-054f4fc95edc",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "dashboard",
    "missing": "",
    "next": "release",
    "phase": "effort-area-link",
    "requirement": "R6",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-30T07:31:18+00:00",
  "relationships": {
    "supersedes": [
      "rec-cd8c245f-4cbf-42d6-b7fa-069685b23c5a"
    ]
  },
  "revision": "sha256:2391a2bf17d034180620eebb6bbd56f86917d6ce8bf15075e37536d0587f0415",
  "subject": "effort-area-link-R6"
}
---

## Evidence

- verify-effort-area-link (R6, tdd): green check-run rec-1eb31a0f-e13a-45f0-9ba3-c72081a1e260 at 25a389b24ced; assertion-level red check-run rec-5c912a91-162c-4cfe-90a1-9ac8d6621b06 (dirty, diff_sha256 set); frozen oracle hashes match at 25a389b24ced

## Missing

none

## Reason

Every check this task runs for R6 passed. For oracle-backed acceptances the assertion-level red, the green at a descendant revision, and the frozen hashes all hold. The phase verification task re-checks R6 later.
