---
{
  "id": "rec-b864e9ae-db02-462b-ae3a-227f4fdf5f0b",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "Phase screen shows the correct tab set; p/s/e open Overview/Spec/Evidence from the main screen; left/right and letter keys switch tabs",
    "effort": "dashboard",
    "method": "tdd",
    "phase": "spec-view",
    "requirement": "R1",
    "verify_command": "uv run --with textual --with pytest python -m pytest tests/test_dashboard_phase_screen.py -q -k \"tab or open or key\""
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-09T20:49:54+00:00",
  "relationships": {},
  "revision": "sha256:e6abfbd27b06de88120125c84d7f36143ea1441fc9da1a5f578426e1a8dbefac",
  "subject": "spec-screen",
  "time": {
    "as_of": "2026-10-09T20:49:54+00:00"
  }
}
---

