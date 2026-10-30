---
{
  "id": "rec-efb3d159-8840-4022-bdf7-bb5baceb9f51",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-dcc4f30b-95bd-4f1c-a345-d667578b0bb1",
    "duration_s": 0.290369,
    "effort": "canon-db-store",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/canon/test_backend_boundary.py::test_open_store_obtains_backend_from_factory"
    ],
    "informed_by": [
      "rec-dcc4f30b-95bd-4f1c-a345-d667578b0bb1"
    ],
    "method": "tdd",
    "output_sha256": "fec8f4f7f19b46c2415772160da675fa189199eef79f1bc19ab26fdd2a93f9ca",
    "requirement": "R3",
    "result": "fail",
    "revision": "0735e6a72f73640ba7c7aea699c9b72f3355b758",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-30T08:45:13+00:00",
  "relationships": {},
  "revision": "sha256:342ef8d97958ec485ef1ea78267deb7e0596010423d063f49cf60acceef9028a",
  "subject": "backend-boundary-r3"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_________________ test_open_store_obtains_backend_from_factory _________________

project = Project(project_root=PosixPath('/tmp/pytest-of-andrewyin/pytest-931/test_open_store_obtains_backen0/repo'), store_path...ndrewyin/pytest-931/test_open_store_obtains_backen0/repo/.canon'), binding=Binding(location='local', source='default'))
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x77fda0dc1940>

    def test_open_store_obtains_backend_from_factory(
        project: Project, monkeypatch: pytest.MonkeyPatch
    ) -> None:
>       calls = _spy_factory(monkeypatch)
                ^^^^^^^^^^^^^^^^^^^^^^^^^

tests/canon/test_backend_boundary.py:206:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
tests/canon/test_backend_boundary.py:186: in _spy_factory
    factory = _factory()
              ^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

    def _factory() -> Callable[..., Any]:
        for name in (
            "orchestra.canon.backend",
            "orchestra.canon.store",
            "orchestra.canon.project",
        ):
            if importlib.util.find_spec(name) is not None:
                factory = getattr(importlib.import_module(name), "open_backend", None)
                if callable(factory):
                    return factory
>       pytest.fail("R3/R4: open_backend must provide the configured storage backend")
E       Failed: R3/R4: open_backend must provide the configured storage backend

tests/canon/test_backend_boundary.py:83: Failed
=========================== short test summary info ============================
FAILED tests/canon/test_backend_boundary.py::test_open_store_obtains_backend_from_factory
1 failed in 0.07s
