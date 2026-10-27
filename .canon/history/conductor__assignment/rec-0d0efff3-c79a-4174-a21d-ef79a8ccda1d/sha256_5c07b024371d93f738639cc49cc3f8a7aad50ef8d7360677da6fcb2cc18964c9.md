---
{
  "id": "rec-0d0efff3-c79a-4174-a21d-ef79a8ccda1d",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "dashboard-features",
    "executor": "sub-task-detail-links",
    "work_item": "task-detail-links"
  },
  "provenance": {
    "sources": [
      "task-detail-links"
    ]
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-02T01:43:01+00:00",
  "relationships": {},
  "revision": "sha256:5c07b024371d93f738639cc49cc3f8a7aad50ef8d7360677da6fcb2cc18964c9",
  "subject": "task-detail-links",
  "time": {
    "observed": "2026-10-02T01:43:01+00:00",
    "recorded": "2026-10-02T01:43:01+00:00"
  }
}
---

## Orientation

Work in /home/ayin/se-workflow/.claude/worktrees/task-detail-links (branch wt/task-detail-links from feat/dashboard-features). Never cd to /home/ayin/se-workflow: another session works there on main. You own TaskDetailScreen and the app-level guards it needs in scripts/dashboard_app.py, plus new tests in tests/test_dashboard_app.py. phase-detail-tasks runs in parallel and changes PhaseDetailScreen: do not touch it. Commit once.
