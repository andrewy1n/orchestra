---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-ae33c19d-d705-4f94-a4d3-cd13fdd72af2",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "bare scripts/check_run.py only; adaptive-artifacts check subcommand (extension)",
    "choice": "Ship a se-workflow CLI shell now with a real check subcommand and room for later commands",
    "effort": "workflow-loop",
    "phase": "check-runner"
  },
  "record_type": "project:decision",
  "recorded_at": "2026-10-10T21:51:40+00:00",
  "relationships": {},
  "revision": "sha256:fada4c3c70fedb9bac98da9ed88bd6b75883dff57c7daf5b9f49812a54187e7a",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "se-workflow-cli",
  "time": {
    "as_of": "2026-10-10T21:51:40+00:00"
  }
}
---

## Rationale

Check-runs are se-workflow policy (acceptance methods, dirty-pass rules, verify-work), not store mechanics. A dedicated `se-workflow` CLI keeps that policy next to the skills and contract, gives agents a stable PATH entry like `dashboard/bin/dashboard`, and leaves room for later commands without growing `adaptive-artifacts`. Introducing the shell now (not only a one-off `check` script) locks the name and layout before more workflow ops accumulate as bare scripts.

## Counter-argument

A single `scripts/check_run.py` would ship faster with less packaging. Putting `check` on `adaptive-artifacts` would reuse one CLI brand. Both keep agents inventing repo-relative paths or coupling verify policy to the runtime's release gate.
