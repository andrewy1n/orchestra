---
{
  "id": "rec-f1a8a4bc-b660-4a70-a32c-adb4a3b3b6a1",
  "lifecycle_state": "active",
  "payload": {
    "effort": "composer",
    "method": "tdd",
    "oracle_hashes": [
      "tests/test_composer_schema.py:sha256:269e7b127f854f80c5e4ed7481d88738699c527e7e36acd472f339de976eb94e"
    ],
    "phase": "composer-schema",
    "requirement": "R1",
    "test_ids": [
      "tests/test_composer_schema.py::test_installed_prefix_entry_point"
    ],
    "verify_command": "python3 -m pytest tests/test_composer_schema.py::test_installed_prefix_entry_point -q"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-27T23:48:21+00:00",
  "relationships": {},
  "revision": "sha256:340a1a628c05ae5bf76e78321611b9a303260bb4815d19c6dcbbceb68a27c564",
  "subject": "verify-composer-schema-entry-point"
}
---

