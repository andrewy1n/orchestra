---
{
  "id": "rec-b43db00d-52de-4ffe-ba39-07011280cbbb",
  "lifecycle_state": "active",
  "payload": {
    "criterion": "The full suite passes, including the tmux tests.",
    "effort": "dashboard",
    "method": "check",
    "phase": "run-facts",
    "requirement": "R1",
    "verify_command": "uv run --with textual --with pytest --with pytest-xdist python -m pytest tests -q -n 4 -m \"not tmux\" && uv run --with textual --with pytest python -m pytest tests -q -m tmux"
  },
  "record_type": "plan:acceptance",
  "recorded_at": "2026-10-05T05:40:02+00:00",
  "relationships": {
    "supersedes": [
      "rec-7d3a31f1-03d8-49c3-b0ec-f57c424da2f5"
    ]
  },
  "revision": "sha256:f4e514207c9b0029dc286296a05ea857161679f74f74a95dd8f8387d0cbd3614",
  "subject": "verify-run-facts-suite",
  "time": {
    "as_of": "2026-10-05T05:40:02+00:00"
  }
}
---

