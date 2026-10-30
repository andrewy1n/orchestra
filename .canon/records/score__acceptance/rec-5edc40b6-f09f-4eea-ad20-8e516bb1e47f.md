---
{
  "id": "rec-5edc40b6-f09f-4eea-ad20-8e516bb1e47f",
  "lifecycle_state": "active",
  "payload": {
    "effort": "dashboard",
    "method": "tdd",
    "oracle_hashes": [
      "tests/dashboard/test_web_packaging.py:sha256:7b2ef3293568d7830ebe1d8849fbf34d1aeeccb08745e9fde294620669ccb264"
    ],
    "phase": "web-packaging",
    "requirement": "R5",
    "test_ids": [
      "tests/dashboard/test_web_packaging.py::test_r5_wheel_job_sets_up_node_and_the_script_checks_the_root"
    ],
    "verify_command": "uv run pytest tests/dashboard/test_web_packaging.py::test_r5_wheel_job_sets_up_node_and_the_script_checks_the_root -q"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-30T01:03:32+00:00",
  "relationships": {},
  "revision": "sha256:905b25088376538a6e116dae28de6c04ca981d36cbdec51d3e3f3133a671e0ef",
  "subject": "dist-in-wheel-smoke"
}
---

