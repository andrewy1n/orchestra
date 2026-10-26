---
{
  "id": "rec-8ca825cb-80c2-47cc-9b12-ebfeb449dca9",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "Verbs, plan-review recognition, prompt text, next-step rules, landing state, Merge branch item, and quiet rule hold in model and gates tests",
    "effort": "dashboard",
    "method": "check",
    "phase": "human-gates",
    "requirement": "R5",
    "verify_command": "uv run --with textual --with pytest python -m pytest tests/test_dashboard_model.py tests/test_dashboard_gates.py -q -k gates"
  },
  "record_type": "plan:acceptance",
  "recorded_at": "2026-10-09T20:44:18+00:00",
  "relationships": {},
  "revision": "sha256:39bb9560f8087dc1d1c30c0a7c9a44f3e12287136cf33a8e54b4581f86971723",
  "subject": "verify-human-gates-model",
  "time": {
    "as_of": "2026-10-09T20:44:18+00:00"
  }
}
---

