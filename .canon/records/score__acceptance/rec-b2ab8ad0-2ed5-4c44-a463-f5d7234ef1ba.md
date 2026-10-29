---
{
  "id": "rec-b2ab8ad0-2ed5-4c44-a463-f5d7234ef1ba",
  "lifecycle_state": "active",
  "payload": {
    "effort": "dashboard",
    "method": "check",
    "phase": "remove-textual",
    "requirement": "R13",
    "verify_command": "uv run python -c \"import sys; sys.modules['textual']=None; import dashboard.backend.server.app, dashboard.backend.server.service\" && uv run pytest tests/test_web_dashboard.py tests/test_web_dashboard_launch.py -q"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-29T20:22:49+00:00",
  "relationships": {},
  "revision": "sha256:65a9413a080532324e6f95f5496cee388e8e267cae8e7e265b20a2867f3ed080",
  "subject": "extract-textual-free"
}
---

