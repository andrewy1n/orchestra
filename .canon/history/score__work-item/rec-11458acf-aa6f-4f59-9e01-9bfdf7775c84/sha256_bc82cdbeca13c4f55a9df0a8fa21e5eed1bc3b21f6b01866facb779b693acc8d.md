---
{
  "id": "rec-11458acf-aa6f-4f59-9e01-9bfdf7775c84",
  "lifecycle_state": "in_progress",
  "payload": {
    "assignee": "parent",
    "effort": "dashboard",
    "kind": "deliver",
    "phase": "dashboard-package",
    "title": "Move the dashboard files into dashboard/"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-02T18:59:19+00:00",
  "relationships": {},
  "revision": "sha256:bc82cdbeca13c4f55a9df0a8fa21e5eed1bc3b21f6b01866facb779b693acc8d",
  "subject": "package-move"
}
---

## Description

Create the top-level `dashboard/` package: `model.py`, `artifact_store.py`, `app.py`, `status.py`, `__main__.py`, `tmux.conf`, `bin/dashboard`, `bin/dashboard-status`. Use `git mv`. Fix imports, the PEP 723 run, the launcher and status entry points, and the test paths and imports. Leave nothing in scripts/.
