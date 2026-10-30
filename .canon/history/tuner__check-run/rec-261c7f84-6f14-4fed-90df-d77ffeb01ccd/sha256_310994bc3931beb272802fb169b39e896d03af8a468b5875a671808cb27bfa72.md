---
{
  "id": "rec-261c7f84-6f14-4fed-90df-d77ffeb01ccd",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-1508996b-307c-41eb-9c7e-3135d692040b",
    "duration_s": 0.270945,
    "effort": "canon-db-store",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/canon/test_backend_boundary.py::test_backend_signatures_never_accept_or_return_file_paths"
    ],
    "informed_by": [
      "rec-1508996b-307c-41eb-9c7e-3135d692040b"
    ],
    "method": "tdd",
    "output_sha256": "7ed912d06c2fc609ced61c5549f784d9f7cb1a395f56210b35e825a8252bfc88",
    "requirement": "R6",
    "result": "fail",
    "revision": "0735e6a72f73640ba7c7aea699c9b72f3355b758",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-30T08:43:33+00:00",
  "relationships": {},
  "revision": "sha256:310994bc3931beb272802fb169b39e896d03af8a468b5875a671808cb27bfa72",
  "subject": "backend-boundary-r6"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
__________ test_backend_signatures_never_accept_or_return_file_paths ___________

    def test_backend_signatures_never_accept_or_return_file_paths() -> None:
>       protocol = _protocol()
                   ^^^^^^^^^^^

tests/canon/test_backend_boundary.py:278:
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
E        +  where None = <function find_spec at 0x77dc04c96de0>('orchestra.canon.backend')
E        +    where <function find_spec at 0x77dc04c96de0> = <module 'importlib.util' (frozen)>.find_spec
E        +      where <module 'importlib.util' (frozen)> = importlib.util

tests/canon/test_backend_boundary.py:58: AssertionError
=========================== short test summary info ============================
FAILED tests/canon/test_backend_boundary.py::test_backend_signatures_never_accept_or_return_file_paths
1 failed in 0.05s
