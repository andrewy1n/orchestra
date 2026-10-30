---
{
  "id": "rec-f68bf6b6-df83-49f1-8ce1-4b97bbeb68af",
  "lifecycle_state": "withdrawn",
  "payload": {
    "effort": "evidence-layer",
    "ordinal": 12,
    "title": "A non-Python runner through the adapter"
  },
  "record_type": "score:phase",
  "recorded_at": "2026-10-30T07:34:05+00:00",
  "relationships": {},
  "revision": "sha256:1c574adacce4a09fa430afce603784b6e26e23aa5713faf2153269ed630f9e59",
  "subject": "second-runner"
}
---

## Problem

The runner adapter is unproven until a non-Python suite runs through it.

## Approach

not yet scoped — discuss when this phase is current. Direction: add one non-Python runner template (vitest or `go test` via gotestsum) and run verdict and `aff audit` against a fixture repo in that language.

## Exit criteria

Decide at plan-phase. At minimum: verdict and the audit's revert step judge claims in a non-Python fixture repo with no change to affidavit modules beyond the template.
