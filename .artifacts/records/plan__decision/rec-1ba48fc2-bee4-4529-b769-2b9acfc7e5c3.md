---
{
  "id": "rec-1ba48fc2-bee4-4529-b769-2b9acfc7e5c3",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "reuse project:decision; stretch assignment-amendment",
    "choice": "new project:oracle-amendment type",
    "effort": "workflow-loop",
    "phase": "oracle-witnesses"
  },
  "record_type": "plan:decision",
  "recorded_at": "2026-10-16T19:47:00+00:00",
  "relationships": {},
  "revision": "sha256:8874822cfdef24a6359f0cb860dfa24f5d514f518362424a38eda02429268516",
  "subject": "oracle-amendment-type",
  "time": {
    "as_of": "2026-10-16T19:47:00+00:00"
  }
}
---

## Rationale

Amendments are per-acceptance hash/file churn with a reason and an approval, not product choices. A dedicated `project:oracle-amendment` type keeps that auditable next to freeze fields and lets close-batch match approvals to hash updates without overloading `project:decision` or `assignment-amendment` (which correct executor briefs, not oracles).

## Counter-argument

Reusing `project:decision` would avoid a new contract type and reuse familiar create/supersede. The cost is the wrong shape: decisions are topic-level choices with alternatives, while oracle amendments are frequent, acceptance-scoped, and must carry old/new hashes for the close gate.
