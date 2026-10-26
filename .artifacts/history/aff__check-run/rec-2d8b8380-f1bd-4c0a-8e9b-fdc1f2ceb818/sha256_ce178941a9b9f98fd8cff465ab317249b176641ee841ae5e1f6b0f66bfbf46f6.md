---
{
  "id": "rec-2d8b8380-f1bd-4c0a-8e9b-fdc1f2ceb818",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-171cb043-59ae-41a2-bd02-431687ff5663",
    "diff_sha256": "5a9cec04e110c03a109863b96b20a53e06ea970cea55e3f6c167c3006a9d8601",
    "duration_s": 2.162951,
    "effort": "dashboard",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_web_dashboard.py::test_r26_refused"
    ],
    "informed_by": [
      "rec-171cb043-59ae-41a2-bd02-431687ff5663"
    ],
    "method": "tdd",
    "output_sha256": "f0a4d569f71d8b74ce66d453b95f3698e1663b39efcd98926304797d4ecaaf46",
    "requirement": "R26",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "web-write-api-r26"
    ]
  },
  "record_type": "aff:check-run",
  "recorded_at": "2026-10-19T06:36:30+00:00",
  "relationships": {},
  "revision": "sha256:ce178941a9b9f98fd8cff465ab317249b176641ee841ae5e1f6b0f66bfbf46f6",
  "subject": "web-write-api-r26",
  "time": {
    "observed": "2026-10-19T06:36:30+00:00",
    "recorded": "2026-10-19T06:36:30+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_______________________________ test_r26_refused _______________________________

store = PosixPath('/tmp/se-workflow-test-vsqgsfwr')
cli = <function cli.<locals>._run at 0x7431cdc5f060>
defs = {'project:active-goal': {'id': 'project:active-goal', 'name': 'active-goal', 'namespace': 'project', 'experimental': F....}, 'project:phase': {'id': 'project:phase', 'name': 'phase', 'namespace': 'project', 'experimental': False, ...}, ...}

    def test_r26_refused(store, cli, defs):
        _seed(cli, defs)
        target = artifact_store.resolve(store)
        snap = _snapshot(target)
        loop = _model_item(snap, "loop-route")
        integration = _model_item(snap, "integration")
        before = model.change_token(target)
        loop_rev = _revision(cli, loop.record_type, loop.id)
        integration_rev = _revision(cli, integration.record_type, integration.id)
>       with _running(store) as (base, _served):
             ^^^^^^^^^^^^^^^

tests/test_web_dashboard.py:380:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
../.local/share/uv/python/cpython-3.13.3-linux-x86_64-gnu/lib/python3.13/contextlib.py:141: in __enter__
    return next(self.gen)
           ^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

store = PosixPath('/tmp/se-workflow-test-vsqgsfwr')

    @contextmanager
    def _running(store):
        target = artifact_store.resolve(store)
        web = _import_web()
>       assert web is not None, "dashboard.web is not importable"
E       AssertionError: dashboard.web is not importable
E       assert None is not None

tests/test_web_dashboard.py:126: AssertionError
=========================== short test summary info ============================
FAILED tests/test_web_dashboard.py::test_r26_refused - AssertionError: dashbo...
1 failed in 1.96s
