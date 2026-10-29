---
{
  "id": "rec-b2ab8ad0-2ed5-4c44-a463-f5d7234ef1ba",
  "lifecycle_state": "active",
  "payload": {
    "effort": "dashboard",
    "method": "check",
    "phase": "remove-textual",
    "requirement": "R13",
    "verify_command": "uv run python -c \"import sys; sys.modules['textual']=None; import dashboard.web.app, dashboard.web.service\" && uv run pytest tests/test_web_dashboard.py tests/test_web_dashboard_launch.py -q"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-29T19:20:26+00:00",
  "relationships": {},
  "revision": "sha256:39b7b85693420bf51c1be27c128af2d59fd6c2a61cf0c10623c28ceb215e2990",
  "subject": "extract-textual-free"
}
---

