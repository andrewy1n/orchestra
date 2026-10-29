---
{
  "id": "rec-0e3caaff-2876-4a9b-bc65-edbc137eae1e",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-f3327213-103f-4fb6-9635-e16de972625e",
    "diff_sha256": "a7a45fa6584df7350c58d307667082ff8a8960601e39ebd31403ca24a920bcdb",
    "duration_s": 0.246196,
    "effort": "ci",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_wheel_smoke.py::test_wheel_smoke_r9_canon_help"
    ],
    "informed_by": [
      "rec-f3327213-103f-4fb6-9635-e16de972625e"
    ],
    "method": "tdd",
    "output_sha256": "9bec30bfeaca381feda5d833f01bf0fee917c4ed7e6ec82e92f5dc42ab9ee77b",
    "requirement": "R9",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T09:18:24+00:00",
  "relationships": {},
  "revision": "sha256:b697cd8a396576e12715780d1e8d14f2ca71ffdbe71652e6463efbb9a62c4efd",
  "subject": "wheel-smoke-script-canon-help"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
________________________ test_wheel_smoke_r9_canon_help ________________________

    def test_wheel_smoke_r9_canon_help():
>       events = _events()
                 ^^^^^^^^^

tests/test_wheel_smoke.py:723:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
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
FAILED tests/test_wheel_smoke.py::test_wheel_smoke_r9_canon_help - AssertionE...
1 failed in 0.04s
