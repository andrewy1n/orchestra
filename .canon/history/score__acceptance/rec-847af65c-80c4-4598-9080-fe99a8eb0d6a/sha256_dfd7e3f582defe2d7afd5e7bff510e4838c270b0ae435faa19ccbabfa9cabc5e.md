---
{
  "id": "rec-847af65c-80c4-4598-9080-fe99a8eb0d6a",
  "lifecycle_state": "active",
  "payload": {
    "effort": "ci",
    "method": "tdd",
    "oracle_hashes": [
      "tests/test_wheel_smoke.py:sha256:7b2d294d69a80da4963e22022debc06efcc860b032e405c04ceb663fd91709ee"
    ],
    "phase": "wheel-smoke",
    "requirement": "R17",
    "test_ids": [
      "tests/test_wheel_smoke.py::test_wheel_smoke_r17_import_installer_adapters"
    ],
    "verify_command": "uv run -q pytest -q -p no:cacheprovider tests/test_wheel_smoke.py::test_wheel_smoke_r17_import_installer_adapters"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-29T09:18:53+00:00",
  "relationships": {},
  "revision": "sha256:dfd7e3f582defe2d7afd5e7bff510e4838c270b0ae435faa19ccbabfa9cabc5e",
  "subject": "wheel-smoke-script-adapters"
}
---

