---
{
  "id": "rec-2c6ee5f7-c7cb-4684-9b5c-d65c7bed255f",
  "lifecycle_state": "asserted",
  "payload": {
    "basis": "test_phase_gate_suite_plugin_defaults asserts a local constant only; this-repo test locks contract to full+advisory",
    "claim": "missing-test on phase-gate-contract: plugin defaults test does not read bundled JSON",
    "effort": "workflow-loop",
    "invalidated_when": "tests assert bundled JSON mode=none separately from this-repo full+advisory pin; reviewer re-run passes",
    "needs": "none"
  },
  "provenance": {
    "sources": [
      "test_phase_gate_suite_plugin_defaults asserts a local constant only; this-repo test locks contract to full+advisory"
    ]
  },
  "record_type": "tuner:finding",
  "recorded_at": "2026-10-15T09:15:14+00:00",
  "relationships": {},
  "revision": "sha256:871f2788fdeaa1dc34b0948b05018e7cf02f5a210163b255afa868c23dd020d6",
  "subject": "review-phase-gate-contract-missing-test"
}
---

## Evidence

expected: self-consistency proves bundled default mode=none from the design file
observed: constant-only assertion; contract locked to full+advisory

## Consequence

Phase merge is blocked until the finding is fixed or cleared.

## Follow-up

Add/adjust tests so R2 can regress-fail.
