---
{
  "id": "rec-e4bef66c-5af6-4e5e-ba1d-fbb840bb24f7",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "Fix and re-run inside the verification task under the 10 minute cap",
    "choice": "A failing verification check is recorded and routed to execute. The verification task does not edit the tree.",
    "effort": "workflow-loop",
    "phase": "verify-budget"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-09T22:23:18+00:00",
  "relationships": {},
  "revision": "sha256:452aa57eef938374482dc7615df8ef600b38f9cf413b007614ad9030e4ebacef",
  "subject": "verify-stop",
  "time": {
    "as_of": "2026-10-09T22:23:18+00:00"
  }
}
---

## Rationale

`verify-human-gates` took 40 minutes and `verify-evidence-view` took 82 minutes because the verification task edited the tree and then ran the checks again. The adopted choice is that a failing check is recorded and routed to execute. The verification executor does not edit code. Execute already owns the repair.

## Counter-argument

A one-line expectation fix is visible from the verification task, and sending it back to execute costs another dispatch. A 10 minute cap could have bounded a repair that stayed inside verification.
