---
{
  "id": "rec-976f8b89-c8c7-4ced-855d-c8c5b3c6c2fb",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "The dashboard files are in dashboard/, none remain in scripts/, and the non-tmux dashboard tests pass at the new paths.",
    "effort": "dashboard",
    "method": "tdd",
    "phase": "dashboard-package",
    "verify_command": "test ! -e scripts/dashboard_app.py && test ! -e scripts/dashboard_model.py && test ! -e scripts/artifact_store.py && uv run --with pytest --with textual pytest tests/test_dashboard_app.py tests/test_dashboard_model.py tests/test_dashboard_launcher.py tests/test_dashboard_status.py tests/test_dashboard_view.py tests/test_dashboard_integration.py"
  },
  "record_type": "plan:acceptance",
  "recorded_at": "2026-10-02T18:57:13+00:00",
  "relationships": {},
  "revision": "sha256:6946562106bba58518db1654068939da42e34ef4514b0ee9a9196101197799a4",
  "subject": "package-move",
  "time": {
    "as_of": "2026-10-02T18:57:13+00:00"
  }
}
---

