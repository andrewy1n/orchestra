---
{
  "id": "rec-3d32e09d-f05b-4f5f-aedf-749d9ae1be97",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-39750da5-4bed-4a37-b46b-012d58a8be55",
    "diff_sha256": "5a9cec04e110c03a109863b96b20a53e06ea970cea55e3f6c167c3006a9d8601",
    "duration_s": 2.492509,
    "effort": "dashboard",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_web_dashboard.py::test_r3_snapshot"
    ],
    "informed_by": [
      "rec-39750da5-4bed-4a37-b46b-012d58a8be55"
    ],
    "method": "tdd",
    "output_sha256": "4d6b5f96457d78b844fadade395ce54d7b3fa7d0f30e72f1a580e1c02ead4293",
    "requirement": "R3",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "web-read-api"
    ]
  },
  "record_type": "aff:check-run",
  "recorded_at": "2026-10-19T06:36:36+00:00",
  "relationships": {},
  "revision": "sha256:5f3b6fd0c7a9f3cae68c02698d22174a0410a1c0b8f1976ab44e417cfb90d445",
  "subject": "web-read-api",
  "time": {
    "observed": "2026-10-19T06:36:36+00:00",
    "recorded": "2026-10-19T06:36:36+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_______________________________ test_r3_snapshot _______________________________

store = PosixPath('/tmp/se-workflow-test-x7d9bfto')
cli = <function cli.<locals>._run at 0x7b3e99be3060>
defs = {'project:active-goal': {'id': 'project:active-goal', 'name': 'active-goal', 'namespace': 'project', 'experimental': F....}, 'project:phase': {'id': 'project:phase', 'name': 'phase', 'namespace': 'project', 'experimental': False, ...}, ...}

    def test_r3_snapshot(store, cli, defs):
        _seed(cli, defs)
        snap = _snapshot(artifact_store.resolve(store))
        assert {item.kind for view in snap.efforts for item in view.needs_you} >= {
            "blocking-question", "needs-human", "unsigned-check", "loop-route", "integration",
        }
        assert any(view.phases for view in snap.efforts)
        assert any(view.tasks for view in snap.efforts)
        assert any(view.backlog for view in snap.efforts)
>       with _running(store) as (base, _target):
             ^^^^^^^^^^^^^^^

tests/test_web_dashboard.py:218:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
../.local/share/uv/python/cpython-3.13.3-linux-x86_64-gnu/lib/python3.13/contextlib.py:141: in __enter__
    return next(self.gen)
           ^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

store = PosixPath('/tmp/se-workflow-test-x7d9bfto')

    @contextmanager
    def _running(store):
        target = artifact_store.resolve(store)
        web = _import_web()
>       assert web is not None, "dashboard.web is not importable"
E       AssertionError: dashboard.web is not importable
E       assert None is not None

tests/test_web_dashboard.py:126: AssertionError
=========================== short test summary info ============================
FAILED tests/test_web_dashboard.py::test_r3_snapshot - AssertionError: dashbo...
1 failed in 2.26s
