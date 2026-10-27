---
{
  "id": "rec-8ea82af0-405d-4dbb-bb7c-a73bdf063adf",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "The skill states that inline minutes in a wave add, a subagent wave uses the longest estimate_minutes, and phase elapsed time adds those wave figures in wave order, skipping blanks.",
    "effort": "dashboard",
    "method": "tdd",
    "phase": "run-facts",
    "requirement": "R4",
    "verify_command": "uv run --with pytest python -m pytest tests/test_estimate_skill.py -q -k rollup"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-05T05:39:22+00:00",
  "relationships": {},
  "revision": "sha256:3d2f8985c86651262e7d9b657e086a794c32638c8c132571464c0f918b03e109",
  "subject": "estimate-skill-rollup",
  "time": {
    "as_of": "2026-10-05T05:39:22+00:00"
  }
}
---

