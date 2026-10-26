---
{
  "id": "rec-7dd7fc71-0bcd-43d1-85f5-7e998fbe20aa",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "the lowest-ordinal in-progress phase",
    "choice": "When several phases are in progress, the default is the one with the most recent activity",
    "effort": "dashboard",
    "phase": "phase-selector"
  },
  "record_type": "plan:decision",
  "recorded_at": "2026-10-05T07:34:08+00:00",
  "relationships": {},
  "revision": "sha256:405a123e60132d3ae6c950dbb0bf68fc9ceeab6cc7b1d73d3521533632cd5f88",
  "subject": "parallel-phase-default",
  "time": {
    "as_of": "2026-10-05T07:34:08+00:00"
  }
}
---

## Rationale

The user chose this. The phase with the latest activity is the one an agent is working in, which is what a glance should show.

## Counter-argument

Lowest ordinal is stable: the default would not flip between phases as two chats record work alternately.
