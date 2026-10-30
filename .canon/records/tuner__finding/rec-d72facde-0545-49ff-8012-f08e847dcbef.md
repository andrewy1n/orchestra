---
{
  "id": "rec-d72facde-0545-49ff-8012-f08e847dcbef",
  "lifecycle_state": "asserted",
  "payload": {
    "basis": "areas.svelte.ts sets items to an empty list when the response is not an array and leaves areas.error empty. It exists so test stubs that answer every URL with the snapshot do not crash.",
    "claim": "missing-test on area-chip-started: the Array.isArray guard in bindAreas has no test and hides a malformed /api/areas response",
    "effort": "dashboard",
    "invalidated_when": "fix lands and reviewer re-run passes, or human clears",
    "needs": "none"
  },
  "record_type": "tuner:finding",
  "recorded_at": "2026-10-30T08:42:10+00:00",
  "relationships": {},
  "revision": "sha256:cd52a219e7d4bfac9580233e2f6c0d4e937901fd3b6b557d710530c4c91fdceb",
  "subject": "review-area-levels-areas-guard"
}
---

## Evidence

areas.svelte.ts sets items to an empty list when the response is not an array and leaves areas.error empty. It exists so test stubs that answer every URL with the snapshot do not crash.

## Consequence

Phase merge is blocked until the finding is fixed or cleared.

## Follow-up

Fix task fix-area-levels-review sets areas.error on a non-array response and adds a test.
