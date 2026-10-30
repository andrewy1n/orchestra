---
{
  "id": "rec-a2ca113d-d61d-49a0-a087-be3c5225af6d",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-e1bbc5dc-033b-4518-927e-1b087f57854d",
    "diff_sha256": "f51f10f87d0011ad03b5cec57c1accc56a79503e82aa878317dcee78917c0136",
    "duration_s": 0.276018,
    "effort": "ci",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_wheel_smoke.py::test_wheel_smoke_r16_import_installer"
    ],
    "informed_by": [
      "rec-e1bbc5dc-033b-4518-927e-1b087f57854d"
    ],
    "method": "tdd",
    "output_sha256": "7c54d91e55e459948fc4868cb5a9a0fd8b84342eeba211e7d2ce79a4629939d0",
    "requirement": "R16",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T09:18:31+00:00",
  "relationships": {},
  "revision": "sha256:dc198beeb5ea45be3efebf0d5f1d3a723237508fa6cea25a9dfb7f0ebbced2b5",
  "subject": "wheel-smoke-script-installer"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
____________________ test_wheel_smoke_r16_import_installer _____________________

    def test_wheel_smoke_r16_import_installer():
>       _assert_import("installer")

tests/test_wheel_smoke.py:803:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
tests/test_wheel_smoke.py:811: in _assert_import
    events = _events()
             ^^^^^^^^^
tests/test_wheel_smoke.py:497: in _events
    return _default_outcome()["events"]
           ^^^^^^^^^^^^^^^^^^
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
FAILED tests/test_wheel_smoke.py::test_wheel_smoke_r16_import_installer - Ass...
1 failed in 0.05s
