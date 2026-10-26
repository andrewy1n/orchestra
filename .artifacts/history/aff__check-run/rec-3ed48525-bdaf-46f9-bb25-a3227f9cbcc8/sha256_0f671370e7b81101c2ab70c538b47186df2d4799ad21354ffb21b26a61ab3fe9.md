---
{
  "id": "rec-3ed48525-bdaf-46f9-bb25-a3227f9cbcc8",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-082c3521-bd06-4066-b644-8e918f6a5f4a",
    "diff_sha256": "c3d9f9bcf0c5e1e73c4a0b2da4bc0eefa1fa1ef1ba7efec2da438f83118b65d3",
    "duration_s": 0.643902,
    "effort": "library-boundary",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_open_store.py::test_r1_git_toplevel"
    ],
    "informed_by": [
      "rec-082c3521-bd06-4066-b644-8e918f6a5f4a"
    ],
    "method": "tdd",
    "output_sha256": "71791795cdee5d7d8dcdcd5c82991eb9e4368b74d8212b7e5338d12b5ac27c1b",
    "requirement": "R1",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "open-store"
    ]
  },
  "record_type": "aff:check-run",
  "recorded_at": "2026-10-21T09:00:54+00:00",
  "relationships": {},
  "revision": "sha256:0f671370e7b81101c2ab70c538b47186df2d4799ad21354ffb21b26a61ab3fe9",
  "subject": "open-store",
  "time": {
    "observed": "2026-10-21T09:00:54+00:00",
    "recorded": "2026-10-21T09:00:54+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_____________________________ test_r1_git_toplevel _____________________________

    def load_open_store():
        try:
>           from adaptive_artifacts.project import open_store
E           ModuleNotFoundError: No module named 'adaptive_artifacts.project'

tests/test_open_store.py:21: ModuleNotFoundError

The above exception was the direct cause of the following exception:

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-75/test_r1_git_toplevel0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x70907a60d5a0>

    def test_r1_git_toplevel(tmp_path, monkeypatch):
>       open_store = load_open_store()

tests/test_open_store.py:152:
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
FAILED tests/test_open_store.py::test_r1_git_toplevel - AssertionError: adapt...
1 failed in 0.05s
