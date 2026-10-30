---
{
  "id": "rec-afaba24b-7ecb-456c-acc9-281e839a1752",
  "lifecycle_state": "asserted",
  "payload": {
    "basis": "exit_code 5; passed counts ['268', '134', '1242']. The configured command ends with pytest -m tmux, which collects nothing.",
    "claim": "advisory suite fail for ui-structure-suite",
    "effort": "dashboard",
    "invalidated_when": "suite check-run passes at phase head, or human clears",
    "needs": "none"
  },
  "record_type": "tuner:finding",
  "recorded_at": "2026-10-29T22:20:22+00:00",
  "relationships": {},
  "revision": "sha256:038835716a036c962cd999e90c7876af061c8767740f7ae11d91a9b922d9b055",
  "subject": "suite-advisory-ui-structure"
}
---

## Evidence

Only the last leg (pytest -m tmux, exit 5) fails; all other legs pass.

## Consequence

Advisory only. The human finding suite-command-tmux-pass tracks the config edit.

## Follow-up

A human drops the tmux pass from settings.conductor.phase_gate.suite.command in .canon/config.json.
