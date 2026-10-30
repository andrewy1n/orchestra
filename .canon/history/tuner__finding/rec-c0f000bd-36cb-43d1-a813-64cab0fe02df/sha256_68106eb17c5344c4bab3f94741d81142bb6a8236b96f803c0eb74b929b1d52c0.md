---
{
  "id": "rec-c0f000bd-36cb-43d1-a813-64cab0fe02df",
  "lifecycle_state": "asserted",
  "payload": {
    "basis": "R8 says effort; the design invariant says the phase ref is set when a phase exists; init creates placeholder phases",
    "claim": "judgment on promote-writers: init promotes with effort only, leaving the idea phase ref empty",
    "effort": "composer",
    "invalidated_when": "the user accepts effort-only promotion on the init path or changes R8",
    "needs": "human"
  },
  "record_type": "tuner:finding",
  "recorded_at": "2026-10-28T07:44:20+00:00",
  "relationships": {},
  "revision": "sha256:68106eb17c5344c4bab3f94741d81142bb6a8236b96f803c0eb74b929b1d52c0",
  "subject": "review-promote-writers-init-phase-ref"
}
---

## Evidence

R8 specifies effort only. The design invariant asks for the phase ref when a phase exists. init creates placeholder phases, not a chosen phase.

## Consequence

Ideas promoted through init carry an effort and no phase ref until a later phase is chosen.

## Follow-up

User decides: keep R8 as written, or have init set the first placeholder phase.
