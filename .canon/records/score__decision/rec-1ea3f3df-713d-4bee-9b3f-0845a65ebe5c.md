---
{
  "id": "rec-1ea3f3df-713d-4bee-9b3f-0845a65ebe5c",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "recheck-only,verdict-only",
    "choice": "verdict-and-recheck",
    "effort": "workflow-loop",
    "phase": "evidence-authority"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-21T06:25:15+00:00",
  "relationships": {},
  "revision": "sha256:540995088727169017a6becef7c1f22068d48090146ab5245dc4db741cba2e8e",
  "subject": "claim-gate-verbs",
  "time": {
    "as_of": "2026-10-21T06:25:15+00:00"
  }
}
---

## Rationale

Skills already require `aff verdict` for oracle/amendment judgment and bind → `aff recheck` before treating a claim as earned. Engine-enforcing both at close matches that prose and closes the hole where a skill skip still yields `done`. The user chose verdict-and-recheck over either verb alone.

## Counter-argument

Enforcing only `aff recheck` (A1b) would be enough if every earned claim were always bound and recheck were the sole gate; verdict would stay a skill discipline. That leaves oracle/amendment judgment unenforced at close when agents skip it.
