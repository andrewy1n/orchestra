---
{
  "id": "rec-f8b9db41-adf1-43db-ba77-14dfb9cca7b7",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-3811bbf0-6494-42e2-ab30-c092aad94cec",
    "diff_sha256": "c3d9f9bcf0c5e1e73c4a0b2da4bc0eefa1fa1ef1ba7efec2da438f83118b65d3",
    "duration_s": 0.528489,
    "effort": "library-boundary",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_open_store.py::test_r9_store_argument_missing_meta"
    ],
    "informed_by": [
      "rec-3811bbf0-6494-42e2-ab30-c092aad94cec"
    ],
    "method": "tdd",
    "output_sha256": "6135b9f77c23f580debaba03a458e45e2663b37e3a07edd25b8522a5d1b9faf5",
    "requirement": "R9",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "open-store-path-missing"
    ]
  },
  "record_type": "aff:check-run",
  "recorded_at": "2026-10-21T09:00:58+00:00",
  "relationships": {},
  "revision": "sha256:1e1ac7e8ac64fccd35b07595d5a79486403d0f9af900314bb6a1c89cab6b12d9",
  "subject": "open-store-path-missing",
  "time": {
    "observed": "2026-10-21T09:00:58+00:00",
    "recorded": "2026-10-21T09:00:58+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_____________________ test_r9_store_argument_missing_meta ______________________

    def load_open_store():
        try:
>           from adaptive_artifacts.project import open_store
E           ModuleNotFoundError: No module named 'adaptive_artifacts.project'

tests/test_open_store.py:21: ModuleNotFoundError

The above exception was the direct cause of the following exception:

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-78/test_r9_store_argument_missing0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7eb90aeff100>

    def test_r9_store_argument_missing_meta(tmp_path, monkeypatch):
>       open_store = load_open_store()

tests/test_open_store.py:277:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

    def load_open_store():
        try:
            from adaptive_artifacts.project import open_store
        except (ImportError, AttributeError) as exc:
>           raise AssertionError(
                "adaptive_artifacts.project.open_store is not available"
            ) from exc
E           AssertionError: adaptive_artifacts.project.open_store is not available

tests/test_open_store.py:23: AssertionError
=========================== short test summary info ============================
FAILED tests/test_open_store.py::test_r9_store_argument_missing_meta - Assert...
1 failed in 0.04s
