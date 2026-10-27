---
{
  "id": "rec-e4ba2299-b1c1-49e1-9b96-347d67c9a8e9",
  "lifecycle_state": "planned",
  "payload": {
    "assignee": "",
    "depends_on": [
      "task-table-module"
    ],
    "effort": "dashboard",
    "kind": "deliver",
    "phase": "dashboard-package",
    "title": "Split the task detail code out of app.py"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-02T18:57:14+00:00",
  "relationships": {},
  "revision": "sha256:8d7d86fb029b9ece19f7c223dfe3cad4b8bbdd24d9eaa8db1b1821c282becbae",
  "subject": "task-detail-module"
}
---

## Description

Move TaskDetailScreen and its helpers (chips, acceptance rows, field splitting, links, body widgets) into `dashboard/task_detail.py`. Keep behavior unchanged. Run after the table split, since both edit app.py.
