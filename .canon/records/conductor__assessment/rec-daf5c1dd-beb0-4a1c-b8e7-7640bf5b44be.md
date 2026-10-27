---
{
  "id": "rec-daf5c1dd-beb0-4a1c-b8e7-7640bf5b44be",
  "lifecycle_state": "active",
  "payload": {
    "confidence": "high",
    "effort": "dashboard",
    "missing": "",
    "next": "release",
    "phase": "estimate-view",
    "requirement": "R6",
    "status": "verified"
  },
  "record_type": "conductor:assessment",
  "recorded_at": "2026-10-05T07:25:31+00:00",
  "relationships": {},
  "revision": "sha256:be291ed52018f252a6ed99d3b4a79c84986e04461a921ce66a49798d21bbee8f",
  "subject": "estimate-view-R6",
  "time": {
    "as_of": "2026-10-05T07:25:31+00:00"
  }
}
---

## Evidence

test_estimate_view_chips failed before the chip change (AssertionError: 'M' not in the chip line) and then passed. A parent re-run of `uv run --with textual --with pytest python -m pytest tests/test_dashboard_estimate.py -q -k estimate_view_chips` passed (1 passed in 2.61s). At 60 columns the sized task shows M, 25m, and executor subagent; the zero-minute inline task shows 0m and executor inline; the unset task shows executor subagent with no size token and no 0m.

## Missing

none

## Reason

The chip pilot passed, so task detail shows size when set, minutes when set including 0m, and the executor.
