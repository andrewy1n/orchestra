---
{
  "base_kind": "event",
  "id": "rec-cb10ecaa-3ad0-4f65-bbed-115695f2befa",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-d32c9db3-448d-4fca-a0aa-d8b10bb49c8a",
    "diff_sha256": "ae50a3bdc47f3e4272aedc31981679624a1bdf5e41c45253c0882a16a099f231",
    "duration_s": 3.963314,
    "effort": "dashboard",
    "exit_code": 1,
    "failing_node_ids": "[\"tests/test_web_dashboard.py::test_r22_reject_note\"]",
    "method": "tdd",
    "output_sha256": "77b708d7a5a8ef7249ce1b96f2fcee6814228331c0fb5f8f4da36f426cd2488a",
    "requirement": "R22",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "web-write-api-r22"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-19T07:48:20+00:00",
  "relationships": {
    "informed_by": [
      "rec-d32c9db3-448d-4fca-a0aa-d8b10bb49c8a",
      "rec-b05401a5-ad1e-45d9-b899-c637d3486ca0"
    ]
  },
  "revision": "sha256:56f43b54fa8048273ab98fc67cf0adb0b735d8d9b3e124f627a5719799842a47",
  "subject": "web-write-api-r22",
  "time": {
    "observed": "2026-10-19T07:48:20+00:00",
    "recorded": "2026-10-19T07:48:20+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_____________________________ test_r22_reject_note _____________________________

store = PosixPath('/tmp/se-workflow-test-m489hrti')
cli = <function cli.<locals>._run at 0x7ff7802c2ac0>
defs = {'project:active-goal': {'id': 'project:active-goal', 'name': 'active-goal', 'namespace': 'project', 'experimental': F....}, 'project:phase': {'id': 'project:phase', 'name': 'phase', 'namespace': 'project', 'experimental': False, ...}, ...}
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7ff7802adcd0>

    def test_r22_reject_note(store, cli, defs, monkeypatch):
        _seed(cli, defs)
        question = _model_item(_snapshot(artifact_store.resolve(store)), "blocking-question")
        assert question.revision and question.revision != "@current"
        calls = []

        def spy(target, item, *, signer=None, action=None, note=None):
            calls.append({"item": item, "action": action, "note": note})

        monkeypatch.setattr(dismiss_module, "dismiss_item", spy)
        with _running(store) as (base, _target):
            page = _page_needs(_get_json(base, "/api/snapshot"), "blocking-question")
            assert page["revision"] == question.revision
            missing = _post(base, "/api/needs", {"id": page["id"], "action": "reject", "revision": page["revision"]})
            blank = _post(base, "/api/needs", {
                "id": page["id"], "action": "reject", "revision": page["revision"], "note": "   ",
            })
            assert missing >= 400 and blank >= 400
            assert calls == []
            noted = _post(base, "/api/needs", {
                "id": page["id"], "action": "reject", "revision": page["revision"], "note": "approach is wrong",
            })
>       assert 200 <= noted < 300, noted
E       AssertionError: 500
E       assert 500 < 300

tests/test_web_dashboard.py:279: AssertionError
----------------------------- Captured stderr call -----------------------------
127.0.0.1 - "GET /api/snapshot HTTP/1.1" 200 -
127.0.0.1 - "POST /api/needs HTTP/1.1" 500 -
127.0.0.1 - "POST /api/needs HTTP/1.1" 500 -
127.0.0.1 - "POST /api/needs HTTP/1.1" 500 -
=========================== short test summary info ============================
FAILED tests/test_web_dashboard.py::test_r22_reject_note - AssertionError: 500
1 failed in 3.65s
