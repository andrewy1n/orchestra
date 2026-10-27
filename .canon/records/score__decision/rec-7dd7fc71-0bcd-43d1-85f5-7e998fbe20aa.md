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
  "record_type": "score:decision",
  "recorded_at": "2026-10-05T07:34:08+00:00",
  "relationships": {},
  "revision": "sha256:eeb5f3158e3202e73e22f18a92da9ce7aaf9d870f6c5874f7eea5837fc1f283e",
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
