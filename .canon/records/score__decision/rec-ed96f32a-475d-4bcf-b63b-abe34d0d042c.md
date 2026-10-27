---
{
  "id": "rec-ed96f32a-475d-4bcf-b63b-abe34d0d042c",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "work-item recorded_at, store history transition timestamps",
    "choice": "Running time counts from the latest assignment for the work-item",
    "effort": "dashboard",
    "phase": "features-task-rows"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-02T03:16:31+00:00",
  "relationships": {},
  "revision": "sha256:84261d073454373cc772491ac8c812a49d610d23e987e9b696c9a7924d3b75df",
  "subject": "running-time-source",
  "time": {
    "as_of": "2026-10-02T01:21:23+00:00"
  }
}
---

## Rationale

Work-item list output carries recorded_at (creation) but no transition times, and the snapshot already lists assignments. The latest assignment for an in-progress task is when execute-phase dispatched it, which is the clock that shows a stuck executor.

## Counter-argument

A task moved to in_progress by hand with no assignment shows no running time, and a re-dispatch resets the clock, hiding total time spent.
