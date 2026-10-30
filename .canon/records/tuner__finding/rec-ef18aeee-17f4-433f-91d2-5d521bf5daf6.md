---
{
  "id": "rec-ef18aeee-17f4-433f-91d2-5d521bf5daf6",
  "lifecycle_state": "asserted",
  "payload": {
    "basis": "Expected R30 on the branch. The edit exists only as an uncommitted change on the primary checkout, because phase commits exclude .canon.",
    "claim": "retire-test-sh: the phase branch still has scripts/test.sh in .canon/config.json",
    "effort": "ci",
    "invalidated_when": "fix lands and the reviewer re-run passes, or a human clears it",
    "needs": "none"
  },
  "record_type": "tuner:finding",
  "recorded_at": "2026-10-29T06:01:07+00:00",
  "relationships": {},
  "revision": "sha256:866fadeead65dfdbcf892149b91371e6fdd75fcd73324e05ac4b797b584b1262",
  "subject": "review-retire-test-sh-behavior-bug"
}
---

## Evidence

Expected R30 on the branch. The edit exists only as an uncommitted change on the primary checkout, because phase commits exclude .canon.

## Consequence

Phase merge is blocked until the finding is fixed or cleared.

## Follow-up

Commit the config.json edit on main, merge main into the phase branch, and rerun the reviewer once.
