---
{
  "id": "rec-3be5902d-b3b7-4898-aadd-eca1add3e308",
  "lifecycle_state": "active",
  "payload": {
    "effort": "dashboard",
    "method": "tdd",
    "oracle_hashes": [
      "tests/test_remove_textual.py:sha256:aa3afc05bd6b842f9de8b782e57fdde7468fd7ba106010dc4cbe5738624548b1"
    ],
    "phase": "remove-textual",
    "requirement": "R2",
    "test_ids": [
      "tests/test_remove_textual.py::test_r2_pyproject_does_not_list_textual"
    ],
    "verify_command": "uv run pytest tests/test_remove_textual.py::test_r2_pyproject_does_not_list_textual -q"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-29T19:22:48+00:00",
  "relationships": {},
  "revision": "sha256:f60abed8447cb83170d6df7caf0ddf4b1750011c55cba7f8f8c515416dd03c29",
  "subject": "delete-textual-ui-pyproject"
}
---

