---
{
  "base_kind": "event",
  "id": "rec-b6cd8012-a7ae-42ac-a3cb-aabff33a7847",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-4330f7e7-99ff-4cc6-be02-27c78971fba1",
    "diff_sha256": "5a9cec04e110c03a109863b96b20a53e06ea970cea55e3f6c167c3006a9d8601",
    "duration_s": 0.35228,
    "effort": "dashboard",
    "exit_code": 1,
    "failing_node_ids": "[\"tests/test_web_dashboard_launch.py::test_r30_serves_build\"]",
    "method": "tdd",
    "output_sha256": "9b9e187edf7471b24b5ad94789d459da2b99882696e46484023e6714fec70832",
    "requirement": "R30",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "web-launcher-r30"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-19T06:36:37+00:00",
  "relationships": {
    "informed_by": [
      "rec-4330f7e7-99ff-4cc6-be02-27c78971fba1"
    ]
  },
  "revision": "sha256:7f134b387cbe7381bf5aac3a9a3d4d59ccf6968957ed6c538629270fe372d629",
  "subject": "web-launcher-r30",
  "time": {
    "observed": "2026-10-19T06:36:37+00:00",
    "recorded": "2026-10-19T06:36:37+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
____________________________ test_r30_serves_build _____________________________

store = PosixPath('/tmp/se-workflow-test-9qb2ewvs')
tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-257/test_r30_serves_build0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x798159349350>

    def test_r30_serves_build(store, tmp_path, monkeypatch):
>       assert SCRIPT.is_file(), f"web launcher missing: {SCRIPT}"
E       AssertionError: web launcher missing: /home/andrewyin/orchestra/dashboard/bin/web
E       assert False
E        +  where False = is_file()
E        +    where is_file = PosixPath('/home/andrewyin/orchestra/dashboard/bin/web').is_file

tests/test_web_dashboard_launch.py:255: AssertionError
=========================== short test summary info ============================
FAILED tests/test_web_dashboard_launch.py::test_r30_serves_build - AssertionE...
1 failed in 0.18s
