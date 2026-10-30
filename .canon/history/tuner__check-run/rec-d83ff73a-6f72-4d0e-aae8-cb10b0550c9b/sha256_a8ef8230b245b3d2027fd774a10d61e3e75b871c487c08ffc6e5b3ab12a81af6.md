---
{
  "id": "rec-d83ff73a-6f72-4d0e-aae8-cb10b0550c9b",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-884ddaaa-ca15-4440-943e-601ccdfb15e6",
    "diff_sha256": "6d4d0acfc04679d42cc5a2b92b0ec06b8849c07df21e1347b5bb652ff1f7a8dc",
    "duration_s": 0.258129,
    "effort": "dashboard",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/dashboard/test_data_layer.py::test_r10_dashboard_tests_live_under_tests_dashboard"
    ],
    "informed_by": [
      "rec-884ddaaa-ca15-4440-943e-601ccdfb15e6"
    ],
    "method": "tdd",
    "output_sha256": "80377d1b4e4798c6edb966e10b5446178ba02cbdb1336ec9a31ae5ae373a94ca",
    "requirement": "R10",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T20:42:02+00:00",
  "relationships": {},
  "revision": "sha256:a8ef8230b245b3d2027fd774a10d61e3e75b871c487c08ffc6e5b3ab12a81af6",
  "subject": "move-dashboard-tests"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_____________ test_r10_dashboard_tests_live_under_tests_dashboard ______________

    def test_r10_dashboard_tests_live_under_tests_dashboard():
        here = TESTS / "dashboard"
        assert here.is_dir(), "missing tests/dashboard/"
>       assert len(list(here.glob("test_*.py"))) >= 6, "tests/dashboard/ holds fewer than 6 test files"
E       AssertionError: tests/dashboard/ holds fewer than 6 test files
E       assert 1 >= 6
E        +  where 1 = len([PosixPath('/home/andrewyin/orchestra/tests/dashboard/test_data_layer.py')])
E        +    where [PosixPath('/home/andrewyin/orchestra/tests/dashboard/test_data_layer.py')] = list(<map object at 0x787113067bb0>)
E        +      where <map object at 0x787113067bb0> = glob('test_*.py')
E        +        where glob = PosixPath('/home/andrewyin/orchestra/tests/dashboard').glob

tests/dashboard/test_data_layer.py:233: AssertionError
=========================== short test summary info ============================
FAILED tests/dashboard/test_data_layer.py::test_r10_dashboard_tests_live_under_tests_dashboard
1 failed in 0.04s
