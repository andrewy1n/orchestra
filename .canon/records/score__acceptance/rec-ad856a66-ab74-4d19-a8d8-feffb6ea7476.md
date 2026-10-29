---
{
  "id": "rec-ad856a66-ab74-4d19-a8d8-feffb6ea7476",
  "lifecycle_state": "active",
  "payload": {
    "effort": "session-handoff",
    "method": "tdd",
    "oracle_hashes": [
      "tests/test_hooks.py:sha256:656488cb920555cd6e6fb70ac1ff9c881df9c739427c69b6e4467205f2284b91"
    ],
    "phase": "hook-context-budget",
    "requirement": "R7",
    "test_ids": [
      "tests/test_hooks.py::test_r7_start_context_has_no_record_id_links"
    ],
    "verify_command": "uv run pytest tests/test_hooks.py::test_r7_start_context_has_no_record_id_links -q -p no:cacheprovider"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-29T08:28:36+00:00",
  "relationships": {},
  "revision": "sha256:75bef3840a89c5c4d9dd49c8706190587c3215b317305a051c92c4df0b977663",
  "subject": "compact-hook-view-links"
}
---

