---
{
  "id": "rec-27e417ee-f73e-4d4e-bbb8-e462d8f1cee4",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "dashboard-ui",
    "executor": "sub-task-detail-model",
    "work_item": "task-detail-model"
  },
  "provenance": {
    "sources": [
      "task-detail-model"
    ]
  },
  "record_type": "run:assignment",
  "recorded_at": "2026-09-30T19:59:14+00:00",
  "relationships": {},
  "revision": "sha256:9825cfba7218ffd29aa97202265dcf41de636b02990f032068fe861575093987",
  "subject": "task-detail-model",
  "time": {
    "observed": "2026-09-30T19:59:14+00:00",
    "recorded": "2026-09-30T19:59:14+00:00"
  }
}
---

## Orientation

Work only in ~/se-workflow on branch feat/dashboard-ui (HEAD 360ebcc). Extend `scripts/dashboard_model.py` and `tests/test_dashboard_model.py`; keep the existing snapshot API unchanged. `list --subject` is exact-or-prefix, so filter to the task slug and `<slug>-<suffix>` records of this effort, and exclude records that belong to another work-item. The next task builds a Textual screen on this loader, so return plain dataclasses with no UI code.
