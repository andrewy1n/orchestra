---
{
  "id": "rec-2830bf8d-0305-4f6a-9ced-6251e2d978d2",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-230d0bb2-0184-4e04-9ba5-1174e9093585",
    "diff_sha256": "04168ff95a3bc04f5cfeda8802c9cfa49b2f25696f519ddfab44274ce831e758",
    "duration_s": 0.25532,
    "effort": "ci",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_wheel_smoke.py::test_wheel_smoke_r5_builds_wheel_when_flag_absent"
    ],
    "informed_by": [
      "rec-230d0bb2-0184-4e04-9ba5-1174e9093585"
    ],
    "method": "tdd",
    "output_sha256": "911ea9384a7c7574707000be8c6560bfc6d13d8a81a56fc3d3ef9d333a29e6b5",
    "requirement": "R5",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T09:18:17+00:00",
  "relationships": {},
  "revision": "sha256:9d3ed0042e3fcbad37225d6b4847dffbdb0777cbefddc87a35cfdb014b05aa7a",
  "subject": "wheel-smoke-script"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
______________ test_wheel_smoke_r5_builds_wheel_when_flag_absent _______________

    def test_wheel_smoke_r5_builds_wheel_when_flag_absent():
>       outcome = _default_outcome()
                  ^^^^^^^^^^^^^^^^^^

tests/test_wheel_smoke.py:683:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
tests/test_wheel_smoke.py:473: in _default_outcome
    script = _script()
             ^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

    def _script() -> Path:
>       assert SCRIPT.is_file(), "missing scripts/wheel_smoke.py"
E       AssertionError: missing scripts/wheel_smoke.py
E       assert False
E        +  where False = is_file()
E        +    where is_file = PosixPath('/home/andrewyin/orchestra/scripts/wheel_smoke.py').is_file

tests/test_wheel_smoke.py:338: AssertionError
=========================== short test summary info ============================
FAILED tests/test_wheel_smoke.py::test_wheel_smoke_r5_builds_wheel_when_flag_absent
1 failed in 0.05s
