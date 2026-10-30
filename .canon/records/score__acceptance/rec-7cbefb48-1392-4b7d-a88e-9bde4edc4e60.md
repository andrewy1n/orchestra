---
{
  "id": "rec-7cbefb48-1392-4b7d-a88e-9bde4edc4e60",
  "lifecycle_state": "active",
  "payload": {
    "effort": "dashboard",
    "method": "tdd",
    "oracle_hashes": [
      "tests/dashboard/test_web_packaging.py:sha256:7b2ef3293568d7830ebe1d8849fbf34d1aeeccb08745e9fde294620669ccb264"
    ],
    "phase": "web-packaging",
    "requirement": "R4",
    "test_ids": [
      "tests/dashboard/test_web_packaging.py::test_r4_installed_wheel_serves_the_index_at_root"
    ],
    "verify_command": "uv run pytest tests/dashboard/test_web_packaging.py::test_r4_installed_wheel_serves_the_index_at_root -q"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-30T01:03:41+00:00",
  "relationships": {},
  "revision": "sha256:bac2708682341387849ea73044c864549ed08a4bd8fc2f04b130be64e967abb0",
  "subject": "verify-web-packaging-r4"
}
---

