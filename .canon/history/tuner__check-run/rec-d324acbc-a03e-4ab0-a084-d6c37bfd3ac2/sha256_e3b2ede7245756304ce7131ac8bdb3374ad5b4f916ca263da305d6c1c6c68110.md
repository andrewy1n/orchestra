---
{
  "id": "rec-d324acbc-a03e-4ab0-a084-d6c37bfd3ac2",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-7a86817f-5f89-4984-895a-d94f86fa0cff",
    "diff_sha256": "5a9cec04e110c03a109863b96b20a53e06ea970cea55e3f6c167c3006a9d8601",
    "duration_s": 0.354725,
    "effort": "dashboard",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_web_dashboard_launch.py::test_r1_loopback"
    ],
    "informed_by": [
      "rec-7a86817f-5f89-4984-895a-d94f86fa0cff"
    ],
    "method": "tdd",
    "output_sha256": "2001e443f205c0334b99e0fd136ee95e376bc717833135d1e4b77c69b7e5bac5",
    "requirement": "R1",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "web-launcher"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-19T06:36:42+00:00",
  "relationships": {},
  "revision": "sha256:e3b2ede7245756304ce7131ac8bdb3374ad5b4f916ca263da305d6c1c6c68110",
  "subject": "web-launcher",
  "time": {
    "observed": "2026-10-19T06:36:42+00:00",
    "recorded": "2026-10-19T06:36:42+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_______________________________ test_r1_loopback _______________________________

store = PosixPath('/tmp/se-workflow-test-0ykd2jpr')
tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-258/test_r1_loopback0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x75353d849350>

    def test_r1_loopback(store, tmp_path, monkeypatch):
>       assert SCRIPT.is_file(), f"web launcher missing: {SCRIPT}"
E       AssertionError: web launcher missing: /home/andrewyin/orchestra/dashboard/bin/web
E       assert False
E        +  where False = is_file()
E        +    where is_file = PosixPath('/home/andrewyin/orchestra/dashboard/bin/web').is_file

tests/test_web_dashboard_launch.py:167: AssertionError
=========================== short test summary info ============================
FAILED tests/test_web_dashboard_launch.py::test_r1_loopback - AssertionError:...
1 failed in 0.19s
