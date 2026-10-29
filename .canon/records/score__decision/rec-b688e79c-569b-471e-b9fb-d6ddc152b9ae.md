---
{
  "id": "rec-b688e79c-569b-471e-b9fb-d6ddc152b9ae",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "constraints of the first live position found (current)",
    "choice": "Show active constraints of every live effort",
    "effort": "session-handoff",
    "phase": "hook-context-budget"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-29T08:13:39+00:00",
  "relationships": {},
  "revision": "sha256:b50f9c37d967311809dd06456c5c5ee992487e85b18e25e9c10f891f1b9a68c9",
  "subject": "hook-constraints-scope"
}
---

## Rationale

The hook took constraints from the first live position it found, so with 11 live efforts the shown set was arbitrary. A session does not know its focus at start, so every live effort's constraints apply until it does.

## Counter-argument

All live efforts' constraints are 17 today and take about 2,900 characters of the budget, which pushes effort sections out sooner. Constraints of efforts the session never touches are noise.
