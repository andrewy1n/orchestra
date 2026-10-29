---
{
  "id": "rec-5d2d358e-4fae-4843-abfc-e936c530ccbe",
  "lifecycle_state": "active",
  "payload": {
    "effort": "ci",
    "method": "tdd",
    "oracle_hashes": [
      "tests/test_wheel_smoke.py:sha256:7b2d294d69a80da4963e22022debc06efcc860b032e405c04ceb663fd91709ee"
    ],
    "phase": "wheel-smoke",
    "requirement": "R14",
    "test_ids": [
      "tests/test_wheel_smoke.py::test_wheel_smoke_r14_import_dashboard"
    ],
    "verify_command": "uv run -q pytest -q -p no:cacheprovider tests/test_wheel_smoke.py::test_wheel_smoke_r14_import_dashboard"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-29T09:18:52+00:00",
  "relationships": {},
  "revision": "sha256:f756d7dcddb2d22584aefe8cd2e83d515875ed1c8cde0363cdd90e0a04b04612",
  "subject": "wheel-smoke-script-dashboard"
}
---

