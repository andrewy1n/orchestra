---
{
  "id": "rec-7ed439b8-f3bf-4aa5-9439-1eaeaf0fa57d",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-85c4cf39-fd64-41fa-8e03-3aa46331d06f",
    "diff_sha256": "ae50a3bdc47f3e4272aedc31981679624a1bdf5e41c45253c0882a16a099f231",
    "duration_s": 4.329221,
    "effort": "dashboard",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_web_dashboard.py::test_r29_backlog_promote"
    ],
    "informed_by": [
      "rec-85c4cf39-fd64-41fa-8e03-3aa46331d06f",
      "rec-b05401a5-ad1e-45d9-b899-c637d3486ca0"
    ],
    "method": "tdd",
    "output_sha256": "8eba66c0e3d5cf0ea00ae4b93084fe7b9d88859bffbd78b615413a23ee720683",
    "requirement": "R29",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "web-write-api-r29"
    ]
  },
  "record_type": "aff:check-run",
  "recorded_at": "2026-10-19T07:48:51+00:00",
  "relationships": {},
  "revision": "sha256:f462d4b9bea0f2c8d3384bdc79de5c014370a67e111991bee884dcffbe2e1a58",
  "subject": "web-write-api-r29",
  "time": {
    "observed": "2026-10-19T07:48:51+00:00",
    "recorded": "2026-10-19T07:48:51+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
___________________________ test_r29_backlog_promote ___________________________

store = PosixPath('/tmp/se-workflow-test-kniu4n6q')
cli = <function cli.<locals>._run at 0x7dc2555eaac0>
defs = {'project:active-goal': {'id': 'project:active-goal', 'name': 'active-goal', 'namespace': 'project', 'experimental': F....}, 'project:phase': {'id': 'project:phase', 'name': 'phase', 'namespace': 'project', 'experimental': False, ...}, ...}
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7dc2555ddcd0>

    def test_r29_backlog_promote(store, cli, defs, monkeypatch):
        _seed(cli, defs)
        parked = _backlog_item(_snapshot(artifact_store.resolve(store)))
        assert parked.status == "open"
        calls = []

        def spy(target, item, *, phase=None):
            calls.append({"target": target, "item": item, "phase": phase})

        monkeypatch.setattr(backlog_module, "promote_item", spy)
        with _running(store) as (base, target):
            page = _get_json(base, "/api/snapshot")
            raw = next(item for view in page["efforts"] for item in view["backlog"] if item["id"] == parked.id)
            status = _post(base, "/api/backlog", {"id": raw["id"], "action": "promote"})
>       assert 200 <= status < 300, status
E       AssertionError: 500
E       assert 500 < 300

tests/test_web_dashboard.py:442: AssertionError
----------------------------- Captured stderr call -----------------------------
127.0.0.1 - "GET /api/snapshot HTTP/1.1" 200 -
127.0.0.1 - "POST /api/backlog HTTP/1.1" 500 -
=========================== short test summary info ============================
FAILED tests/test_web_dashboard.py::test_r29_backlog_promote - AssertionError...
1 failed in 4.01s
