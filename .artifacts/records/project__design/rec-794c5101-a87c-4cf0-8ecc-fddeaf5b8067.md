---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-794c5101-a87c-4cf0-8ecc-fddeaf5b8067",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "decisions": "phase-gate-shape,suite-plugin-defaults,se-workflow-suite-policy,red-first-scope,suite-policy-authority",
    "effort": "workflow-loop",
    "phase": "verification-policy"
  },
  "record_type": "project:design",
  "recorded_at": "2026-10-15T08:38:58+00:00",
  "relationships": {},
  "revision": "sha256:027df177e755e1f9f4de635a8a0fb1484edc627467949cdf10287faa975f14f1",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "verification-policy",
  "time": {
    "as_of": "2026-10-15T08:38:58+00:00"
  }
}
---

## Architecture

Replace the hardcoded tier-2 invariant with a contracted `phase_gate.suite` block on `project-design.json`. Skills and the Python runner load that block at phase end.

```
phase_gate.suite.mode: none | smoke | full | external
phase_gate.suite.command: string (shell command for smoke/full; empty when none/external)
phase_gate.suite.gate: required | advisory | deferred
```

Phase-end order for structured work stays: closing verification → reviewer → integration-report → suite (if mode ≠ none and gate ≠ deferred) → Landing gate.

Check-run convention: subject `<phase-slug>-suite`, `evidence_kind` appropriate to the command (typically `integration`), `revision` = phase head. Dashboard reads the new subject (keep a short migration note for old `-tier2` subjects if needed for display only).

Gate composition:
- Always (structured): task acceptances@head + review@head
- Suite: per contracted gate hardness
- Incidental: skip review + suite

## Interfaces

- `contract/project-design.json` (+ live `.artifacts/project-design.json` / resolve): `phase_gate` block; this repo pins full+advisory + README command.
- `skills/execute-phase/SKILL.md`: read policy; rename tier-2 steps; advisory/deferred behavior.
- `se_workflow/tier2.py` (rename or wrap as suite): start/poll/record using contracted command.
- `dashboard/model.py`: suite status label from `<phase>-suite`.
- README Testing / verification sections; `tests/test_tiered_verification.py`, `tests/test_verify_budget.py`, dashboard suite tests, `tests/test_skill_contract_consistency.py`.

## Decisions

- phase-gate-shape: contract top-level phase_gate
- suite-plugin-defaults: mode=none; configured suites default gate=required
- se-workflow-suite-policy: this repo full+advisory
- red-first-scope: tdd only
- suite-policy-authority: human contract / agent enforce

## Invariants

- No agent waiver of contracted suite policy.
- No whole-suite per-task verify_command.
- Red-first unchanged for tdd.

## Assumptions

- Top-level `phase_gate` is tolerated by resolve the same way `assessment` is.
- Rename of module/subjects can ship in one phase without keeping dual writers.

## Tradeoffs

- Advisory full suite on this repo: visibility without merge blockage vs weaker local safety before Landing.
- Default none for plugins: safe for strangers vs silent lack of regression until configured.

## Risks

- Old `-tier2` check-runs confuse dashboard until migration/display fallback is handled.
- Contract resolve/pin steps forgotten after editing design → digest drift (use local store + resolve).
- Advisory failures ignored by humans — mitigate with finding + dashboard status.
