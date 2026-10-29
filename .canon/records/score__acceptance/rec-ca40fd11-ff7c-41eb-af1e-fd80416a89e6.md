---
{
  "id": "rec-ca40fd11-ff7c-41eb-af1e-fd80416a89e6",
  "lifecycle_state": "active",
  "payload": {
    "effort": "dashboard",
    "method": "tdd",
    "oracle_hashes": [
      "tests/dashboard/test_data_layer.py:sha256:86ff0ac891e32708da3c09b2afcf5b23ec09754e76dd70a2290a8e4268c38ac2"
    ],
    "phase": "data-layer",
    "requirement": "R9",
    "test_ids": [
      "tests/dashboard/test_data_layer.py::test_r9_ui_imports_api_types_and_types_ts_holds_no_api_shape"
    ],
    "verify_command": "uv run pytest tests/dashboard/test_data_layer.py::test_r9_ui_imports_api_types_and_types_ts_holds_no_api_shape -q"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-29T20:42:06+00:00",
  "relationships": {},
  "revision": "sha256:6d204440a671147db1c946588fe53704ad320ea5a31e753c1eac2338aecf062a",
  "subject": "verify-data-layer-r9"
}
---

