---
{
  "id": "rec-6f7a1c39-fa5a-4a7d-bea2-202f90d870ed",
  "lifecycle_state": "active",
  "payload": {
    "effort": "ci",
    "method": "tdd",
    "oracle_hashes": [
      "tests/test_wheel_smoke.py:sha256:c3117f02208329848501bf5dd4ca813a76522b670b37dd327d04f7dde7cf1277"
    ],
    "phase": "wheel-smoke",
    "requirement": "R6",
    "test_ids": [
      "tests/test_wheel_smoke.py::test_wheel_smoke_r6_installs_into_new_venv"
    ],
    "verify_command": "uv run -q pytest -q -p no:cacheprovider tests/test_wheel_smoke.py::test_wheel_smoke_r6_installs_into_new_venv"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-30T00:58:06+00:00",
  "relationships": {},
  "revision": "sha256:58b347ba8ec854c52f3c3b453241710adf0db0d0d07de591b65e8b6e2ab9eeaf",
  "subject": "wheel-smoke-script-venv"
}
---

