---
{
  "id": "rec-df8dad20-f7fc-468f-bed9-b09bf272658b",
  "lifecycle_state": "active",
  "payload": {
    "effort": "composer",
    "method": "tdd",
    "oracle_hashes": [
      "tests/test_composer_schema.py:sha256:269e7b127f854f80c5e4ed7481d88738699c527e7e36acd472f339de976eb94e"
    ],
    "phase": "composer-schema",
    "requirement": "R3",
    "test_ids": [
      "tests/test_composer_schema.py::test_installed_prefix_ships_composer_json"
    ],
    "verify_command": "python3 -m pytest tests/test_composer_schema.py::test_installed_prefix_ships_composer_json -q"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-27T23:48:25+00:00",
  "relationships": {},
  "revision": "sha256:7908b7cd70817bc9207c3c3fd0a99408657d41f642c664dee70fc37a40a089dd",
  "subject": "verify-composer-schema-package-data"
}
---

