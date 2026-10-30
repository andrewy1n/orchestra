---
{
  "id": "rec-9b0adaf1-c4cc-4587-adcb-50f5f3e8a414",
  "lifecycle_state": "active",
  "payload": {
    "effort": "ci",
    "method": "tdd",
    "oracle_hashes": [
      "tests/test_wheel_smoke.py:sha256:c3117f02208329848501bf5dd4ca813a76522b670b37dd327d04f7dde7cf1277"
    ],
    "phase": "wheel-smoke",
    "requirement": "R19",
    "test_ids": [
      "tests/test_wheel_smoke.py::test_wheel_smoke_r19_missing_providers_json"
    ],
    "verify_command": "uv run -q pytest -q -p no:cacheprovider tests/test_wheel_smoke.py::test_wheel_smoke_r19_missing_providers_json"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-30T00:58:13+00:00",
  "relationships": {},
  "revision": "sha256:46f3d24112a5553d0e567a50ff0ddafdd197fa19b25f12532325d7ad2c845cae",
  "subject": "wheel-smoke-script-providers"
}
---

