---
{
  "id": "rec-dbece29d-2cc1-4ae8-99dc-300a3b7c8e3a",
  "lifecycle_state": "active",
  "payload": {
    "effort": "library-boundary",
    "method": "tdd",
    "oracle_hashes": [
      "tests/test_open_store.py:sha256:d601c17196a93a7bcfc4ee5f461e5ab749d071b3575b111b1536d8144a596afd"
    ],
    "phase": "aa-library",
    "requirement": "R6",
    "test_ids": [
      "tests/test_open_store.py::test_r6_committed_binding_file"
    ],
    "verify_command": "PYTHONPATH=src python3 -m pytest tests/test_open_store.py::test_r6_committed_binding_file -q"
  },
  "record_type": "plan:acceptance",
  "recorded_at": "2026-10-21T09:01:15+00:00",
  "relationships": {},
  "revision": "sha256:9dfa5fe696bacf60bf108b106204d01674f6d3f963f46150074e6c168cf483e2",
  "subject": "open-store-committed-binding",
  "time": {
    "as_of": "2026-10-21T08:48:20+00:00"
  }
}
---

