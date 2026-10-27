---
{
  "id": "rec-323fc48e-f2ba-4fcf-bea1-344c61a9f338",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "Opening the phase screen from the dashboard entry shows tabs and Spec Markdown for a seeded structured phase",
    "effort": "dashboard",
    "method": "check",
    "phase": "spec-view",
    "requirement": "R2",
    "verify_command": "uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py tests/test_dashboard_integration.py -q -k \"phase_screen or once\""
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-09T20:49:54+00:00",
  "relationships": {},
  "revision": "sha256:154cf0ccf775066d728db6a8d456433b759e8b0338aac7ef273ea15ec0b5e63f",
  "subject": "verify-spec-view",
  "time": {
    "as_of": "2026-10-09T20:49:54+00:00"
  }
}
---

