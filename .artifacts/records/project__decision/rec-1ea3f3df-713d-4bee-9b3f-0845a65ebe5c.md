---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-1ea3f3df-713d-4bee-9b3f-0845a65ebe5c",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "recheck-only,verdict-only",
    "choice": "verdict-and-recheck",
    "effort": "workflow-loop",
    "phase": "evidence-authority"
  },
  "record_type": "project:decision",
  "recorded_at": "2026-10-21T06:25:15+00:00",
  "relationships": {},
  "revision": "sha256:099e5bc171e8d78919ce1cb4df106ae0e87092a1dd9cb2fc5cea9466f8d73a8d",
  "stewardship": {
    "steward": "agent"
  },
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
