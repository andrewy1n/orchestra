---
{
  "id": "rec-9ba85175-35a9-4ffe-ae9c-ab68ca062aae",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "inline",
    "decisions": [
      "ci-python-version"
    ],
    "depends_on": [
      "fix-review-minors"
    ],
    "effort": "ci",
    "estimate_minutes": 10,
    "executor": "inline",
    "kind": "deliver",
    "phase": "ci-workflow",
    "requirements": [
      "R27"
    ],
    "size": "S",
    "title": "Pin the dashboard guards and harden the worker wait"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-29T06:56:08+00:00",
  "relationships": {},
  "revision": "sha256:d68cffe138de77e4d18a33041729843d54886c2dc0ad3215db7a79939ad79499",
  "subject": "fix-review-tests"
}
---

## Description

R27: Every blocking job passes on a pull request from the phase branch.

The phase-end reviewer found the dashboard teardown guards unpinned and the worker-wait helpers inconsistent. The user chose to add tests, keep the guards, and fix the helpers.

## Approach

Add `tests/test_dashboard_guards.py`. Subclass `NeedsYouDetailScreen` and `EffortPane` with a stubbed `query` and `_show` so no app is needed. Cover: `show` swallows `NoMatches` when a panel is missing; `show` re-raises `NoMatches` when every panel in `NEEDS_PANELS` is present; `follow` does nothing before `ready`; `EffortPane.show` returns when `#goal` is absent. Make `tests/helpers.py` `wait_workers` raise `AssertionError` when every retry hits `WorkerCancelled`. Make `_wait_workers` in `tests/test_dashboard_app.py` call `h.wait_workers`. Prove each guard test fails when its guard is removed. Run the dashboard test files and ruff. Commit on the task branch.
