---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-e3f793aa-d204-44b7-bb81-d44c6afbc4e4",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "checked-in-fixture, per-repo-smokes",
    "choice": "generated-temp-repo",
    "effort": "library-boundary",
    "phase": "library-e2e"
  },
  "record_type": "project:decision",
  "recorded_at": "2026-10-21T08:36:52+00:00",
  "relationships": {},
  "revision": "sha256:e044f2a3e808f0e4e1739034aabdf99653c51ca6e0ec6ebd61dfcc46bea287b0",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "e2e-temp-repo",
  "time": {
    "as_of": "2026-10-21T08:36:52+00:00"
  }
}
---

## Rationale

The user chose a generated temporary repository and one orchestra test. Orchestra is the only package that calls the other two, so the proof that the Python close and the commands agree belongs here. A generated repo needs no fixture upkeep.

## Counter-argument

A checked-in fixture is easier to open and rerun by hand when the test fails. The cost is a second store to keep valid as the contract changes, beside the one the test can build.
