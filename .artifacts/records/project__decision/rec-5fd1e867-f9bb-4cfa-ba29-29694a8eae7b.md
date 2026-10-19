---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-5fd1e867-f9bb-4cfa-ba29-29694a8eae7b",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "one subagent per requirement",
    "choice": "one oracle-author subagent per phase",
    "effort": "workflow-loop",
    "phase": "oracle-witnesses"
  },
  "record_type": "project:decision",
  "recorded_at": "2026-10-16T19:46:59+00:00",
  "relationships": {},
  "revision": "sha256:dcf0ced20d0053a708f8b5d1772895f8b7661501373f50f4d77e738f2a3f35c7",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "oracle-author-grain",
  "time": {
    "as_of": "2026-10-16T19:46:59+00:00"
  }
}
---

## Rationale

One oracle-author subagent for the whole phase cuts dispatch cost and keeps plan-phase reviewable as a single oracle wave. Isolation still comes from the brief (spec/requirement text only, no implementation) and from freezing per acceptance, not from spawning N authors.

## Counter-argument

One subagent per requirement would maximize isolation and stop cross-requirement leakage or "helpful" shared fixtures that weaken a single claim. The cost is N dispatches, N reds, and more amendment surface for the same phase — heavier than this phase needs for the first enforced oracle loop.
