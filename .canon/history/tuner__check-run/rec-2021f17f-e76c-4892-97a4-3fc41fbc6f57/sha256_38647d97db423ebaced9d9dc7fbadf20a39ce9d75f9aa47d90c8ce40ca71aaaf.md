---
{
  "id": "rec-2021f17f-e76c-4892-97a4-3fc41fbc6f57",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-a29f2aa4-6322-4d68-92e9-a3fc7ddd1e3e",
    "duration_s": 0.235738,
    "effort": "canon-db-store",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/canon/test_backend_boundary.py::test_backend_protocol_declares_operations_used_by_callers"
    ],
    "informed_by": [
      "rec-a29f2aa4-6322-4d68-92e9-a3fc7ddd1e3e"
    ],
    "method": "tdd",
    "output_sha256": "dc77eb16e5b899dd0bc6bd77f6dda2c5e914f354938ddf684442319a3ce3a69e",
    "requirement": "R1",
    "result": "fail",
    "revision": "0735e6a72f73640ba7c7aea699c9b72f3355b758",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-30T08:44:06+00:00",
  "relationships": {},
  "revision": "sha256:38647d97db423ebaced9d9dc7fbadf20a39ce9d75f9aa47d90c8ce40ca71aaaf",
  "subject": "backend-boundary"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
__________ test_backend_protocol_declares_operations_used_by_callers ___________

    def test_backend_protocol_declares_operations_used_by_callers() -> None:
>       protocol = _protocol()
                   ^^^^^^^^^^^

tests/canon/test_backend_boundary.py:105:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
tests/canon/test_backend_boundary.py:65: in _protocol
    protocol = getattr(_backend_module(), "Backend", None)
                       ^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

    def _backend_module() -> ModuleType:
>       assert importlib.util.find_spec("orchestra.canon.backend") is not None, (
            "R1: backend.py must define Backend"
        )
E       AssertionError: R1: backend.py must define Backend
E       assert None is not None
E        +  where None = <function find_spec at 0x7a53bd096de0>('orchestra.canon.backend')
E        +    where <function find_spec at 0x7a53bd096de0> = <module 'importlib.util' (frozen)>.find_spec
E        +      where <module 'importlib.util' (frozen)> = importlib.util

tests/canon/test_backend_boundary.py:58: AssertionError
=========================== short test summary info ============================
FAILED tests/canon/test_backend_boundary.py::test_backend_protocol_declares_operations_used_by_callers
1 failed in 0.03s
