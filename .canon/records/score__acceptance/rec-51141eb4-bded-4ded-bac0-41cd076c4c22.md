---
{
  "id": "rec-51141eb4-bded-4ded-bac0-41cd076c4c22",
  "lifecycle_state": "active",
  "payload": {
    "effort": "dashboard",
    "method": "tdd",
    "oracle_hashes": [
      "tests/test_ci_workflow.py:sha256:00fefe4157094c1eedb9efd6467983a10734c1a43b25ad767abcfa2f20574d5b"
    ],
    "phase": "node-ci",
    "requirement": "R2",
    "test_ids": [
      "tests/test_ci_workflow.py::test_r2_web_job_has_no_path_filter"
    ],
    "verify_command": "uv run pytest tests/test_ci_workflow.py::test_r2_web_job_has_no_path_filter -q"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-29T18:52:59+00:00",
  "relationships": {},
  "revision": "sha256:01a19c0409f4e6009097673567a4ff05cf800ba74b8260e506c545c77125dcea",
  "subject": "verify-node-ci-nopath"
}
---

