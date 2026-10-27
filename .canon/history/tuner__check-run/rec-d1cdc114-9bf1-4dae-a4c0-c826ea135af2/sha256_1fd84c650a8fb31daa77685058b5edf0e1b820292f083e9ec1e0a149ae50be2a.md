---
{
  "id": "rec-d1cdc114-9bf1-4dae-a4c0-c826ea135af2",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-af1deece-a7c4-410c-884c-7ba4ae9aa0c7",
    "diff_sha256": "c3d9f9bcf0c5e1e73c4a0b2da4bc0eefa1fa1ef1ba7efec2da438f83118b65d3",
    "duration_s": 0.592161,
    "effort": "library-boundary",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_project_ops.py::test_r18_create"
    ],
    "informed_by": [
      "rec-af1deece-a7c4-410c-884c-7ba4ae9aa0c7"
    ],
    "method": "tdd",
    "output_sha256": "bc3be92a2ba795786968024ede7382ccfbaa369fd510992f8fae07b4eb0d7834",
    "requirement": "R18",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "project-ops-create"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-21T09:01:09+00:00",
  "relationships": {},
  "revision": "sha256:1fd84c650a8fb31daa77685058b5edf0e1b820292f083e9ec1e0a149ae50be2a",
  "subject": "project-ops-create",
  "time": {
    "observed": "2026-10-21T09:01:09+00:00",
    "recorded": "2026-10-21T09:01:09+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_______________________________ test_r18_create ________________________________

    def load_open_store():
        try:
>           from adaptive_artifacts.project import open_store
E           ModuleNotFoundError: No module named 'adaptive_artifacts.project'

tests/test_project_ops.py:27: ModuleNotFoundError

The above exception was the direct cause of the following exception:

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-87/test_r18_create0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x75325016a5c0>

    def test_r18_create(tmp_path, monkeypatch):
>       load_open_store()

tests/test_project_ops.py:219:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

    def load_open_store():
        try:
            from adaptive_artifacts.project import open_store
        except (ImportError, AttributeError) as exc:
>           raise AssertionError(
                "adaptive_artifacts.project.open_store is not available"
            ) from exc
E           AssertionError: adaptive_artifacts.project.open_store is not available

tests/test_project_ops.py:29: AssertionError
=========================== short test summary info ============================
FAILED tests/test_project_ops.py::test_r18_create - AssertionError: adaptive_...
1 failed in 0.05s
