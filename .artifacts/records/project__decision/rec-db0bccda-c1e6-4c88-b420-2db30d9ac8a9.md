---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-db0bccda-c1e6-4c88-b420-2db30d9ac8a9",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "detected-native-fallback,all-providers",
    "choice": "detected-require-choice",
    "effort": "packaging",
    "phase": "installer-wizard"
  },
  "record_type": "project:decision",
  "recorded_at": "2026-10-19T03:08:33+00:00",
  "relationships": {},
  "revision": "sha256:9c843ab7e6c5a0fabb3261de30ff9fa702d98f5cb525e007082fcb71493e5c52",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "installer-default-detected",
  "time": {
    "as_of": "2026-10-19T03:08:33+00:00"
  }
}
---

## Rationale

The current default selects every provider, which is why a run in the orchestra checkout wrote eight host directories. Defaulting to detected hosts makes the command safe on a clean project, and refusing when nothing is detected forces the user to choose explicitly instead of guessing. `--all` remains the explicit way to install every provider.

## Counter-argument

Falling back to the native three hosts would make the first run more productive on a clean checkout, and keeping the current default-all behavior is the least disruptive change. Both write directories the user did not ask for, which is the failure this phase exists to fix.
