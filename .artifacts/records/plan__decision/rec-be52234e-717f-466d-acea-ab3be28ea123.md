---
{
  "id": "rec-be52234e-717f-466d-acea-ab3be28ea123",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "agent may waive; mid-flight store claim supersede without contract edit",
    "choice": "human owns policy via contract; agent only enforces",
    "effort": "workflow-loop",
    "phase": "verification-policy"
  },
  "record_type": "plan:decision",
  "recorded_at": "2026-10-15T08:38:30+00:00",
  "relationships": {},
  "revision": "sha256:58b1469bc2c657621a6102eed37f029de4620fcd467ed459449d929d9d32120c",
  "subject": "suite-policy-authority",
  "time": {
    "as_of": "2026-10-15T08:38:30+00:00"
  }
}
---

## Rationale

Agents must not skip or weaken a configured suite because it is slow. Humans change policy by editing the contract (and re-resolving). Agents execute mode/command/gate as written: run when configured, enforce required, record-and-continue for advisory, surface deferred as a Landing human stop.

## Counter-argument

Allowing a one-phase human override without a contract edit would be faster under flake pressure. That reopens "who decided to skip?" across sessions; Needs-you plus an explicit contract change is slower but auditable.
