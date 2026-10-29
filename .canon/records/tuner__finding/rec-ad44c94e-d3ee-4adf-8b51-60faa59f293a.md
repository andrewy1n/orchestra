---
{
  "id": "rec-ad44c94e-d3ee-4adf-8b51-60faa59f293a",
  "lifecycle_state": "asserted",
  "payload": {
    "basis": "live_efforts unions GOAL and POSITION selections; the spec assumption names score:effort only",
    "claim": "spec-gap on compact-hook-view: live_efforts counts a non-closed position even when its effort goal is closed or missing",
    "effort": "session-handoff",
    "invalidated_when": "fix lands and reviewer re-run passes, or a human clears it",
    "needs": "none"
  },
  "record_type": "tuner:finding",
  "recorded_at": "2026-10-29T09:06:11+00:00",
  "relationships": {},
  "revision": "sha256:5a9ca9296c1de3c8c1aa8e26911e81650075de42accb22b3181831db5567e9e8",
  "subject": "review-compact-hook-view-spec-gap"
}
---

## Evidence

Expected live efforts to be active score:effort records whose status is not closed. Observed: an open position alone makes an effort live and feeds sections and constraints.

## Consequence

Phase merge is blocked until the finding is fixed or cleared.

## Follow-up

Fix task fix-hook-dropped-groups.
