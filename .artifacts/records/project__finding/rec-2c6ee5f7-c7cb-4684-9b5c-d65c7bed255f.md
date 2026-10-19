---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-2c6ee5f7-c7cb-4684-9b5c-d65c7bed255f",
  "identity": "unknown",
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
  "record_type": "project:finding",
  "recorded_at": "2026-10-15T09:15:14+00:00",
  "relationships": {},
  "revision": "sha256:ff411661453efd0687f25e479bc1cef1adcefbfbba8f1cd0655e214618ab8006",
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
