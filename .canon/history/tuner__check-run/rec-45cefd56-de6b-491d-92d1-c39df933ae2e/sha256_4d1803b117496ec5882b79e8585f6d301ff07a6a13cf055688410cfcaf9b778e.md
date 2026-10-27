---
{
  "id": "rec-45cefd56-de6b-491d-92d1-c39df933ae2e",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-5f4505cf-d588-401b-a1e7-0266390e1d70",
    "diff_sha256": "c3d9f9bcf0c5e1e73c4a0b2da4bc0eefa1fa1ef1ba7efec2da438f83118b65d3",
    "duration_s": 0.590598,
    "effort": "library-boundary",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_project_ops.py::test_r16_get_missing"
    ],
    "informed_by": [
      "rec-5f4505cf-d588-401b-a1e7-0266390e1d70"
    ],
    "method": "tdd",
    "output_sha256": "236a06df70c80fc4eeb35929a8ee16d1c709c13e485ffc8db4605e319e123ca6",
    "requirement": "R16",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "project-ops-missing"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-21T09:01:03+00:00",
  "relationships": {},
  "revision": "sha256:4d1803b117496ec5882b79e8585f6d301ff07a6a13cf055688410cfcaf9b778e",
  "subject": "project-ops-missing",
  "time": {
    "observed": "2026-10-21T09:01:03+00:00",
    "recorded": "2026-10-21T09:01:03+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_____________________________ test_r16_get_missing _____________________________

    def load_open_store():
        try:
>           from adaptive_artifacts.project import open_store
E           ModuleNotFoundError: No module named 'adaptive_artifacts.project'

tests/test_project_ops.py:27: ModuleNotFoundError

The above exception was the direct cause of the following exception:

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-82/test_r16_get_missing0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7780b8f0e560>

    def test_r16_get_missing(tmp_path, monkeypatch):
>       load_open_store()

tests/test_project_ops.py:181:
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
FAILED tests/test_project_ops.py::test_r16_get_missing - AssertionError: adap...
1 failed in 0.04s
