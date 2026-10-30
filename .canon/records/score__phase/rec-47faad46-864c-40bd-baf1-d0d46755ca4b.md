---
{
  "id": "rec-47faad46-864c-40bd-baf1-d0d46755ca4b",
  "lifecycle_state": "withdrawn",
  "payload": {
    "effort": "evidence-layer",
    "ordinal": 13,
    "title": "End to end on an external repo and through orchestra"
  },
  "record_type": "score:phase",
  "recorded_at": "2026-10-30T07:34:04+00:00",
  "relationships": {},
  "revision": "sha256:4a1cca209f98f5c0f27bb4ca24ea60c71b507fcd7cd9cc703b910a744622d0fc",
  "subject": "evidence-e2e"
}
---

## Problem

The manifest, verdict, attestation, provenance, and audit only prove themselves together, on a repo that is not this one and through a client that is not affidavit.

## Approach

not yet scoped — decide at plan-phase. Direction: run the full loop on an external repo with no orchestra (claim add, freeze, oracle commit, implement, signed verdict in CI, audit), and run orchestra's deliver loop from a phase worktree against `aff verdict` and `aff audit`.

## Exit criteria

Decide at plan-phase. At minimum: an integration test drives both paths end to end and a gate accepts only the signed verdict.
