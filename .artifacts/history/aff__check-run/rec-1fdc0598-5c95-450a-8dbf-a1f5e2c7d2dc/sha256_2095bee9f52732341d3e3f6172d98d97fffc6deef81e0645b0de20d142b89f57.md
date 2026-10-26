---
{
  "id": "rec-1fdc0598-5c95-450a-8dbf-a1f5e2c7d2dc",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-be370437-14d1-4c3e-8316-a940155e8cec",
    "diff_sha256": "ae50a3bdc47f3e4272aedc31981679624a1bdf5e41c45253c0882a16a099f231",
    "duration_s": 4.626074,
    "effort": "dashboard",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_web_dashboard.py::test_r24_signer"
    ],
    "informed_by": [
      "rec-be370437-14d1-4c3e-8316-a940155e8cec",
      "rec-b05401a5-ad1e-45d9-b899-c637d3486ca0"
    ],
    "method": "tdd",
    "output_sha256": "d3c1963266a327894835478918f229d586a99b51285a565b3ec89ba59bc46fde",
    "requirement": "R24",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "web-write-api-r24"
    ]
  },
  "record_type": "aff:check-run",
  "recorded_at": "2026-10-19T07:48:30+00:00",
  "relationships": {},
  "revision": "sha256:2095bee9f52732341d3e3f6172d98d97fffc6deef81e0645b0de20d142b89f57",
  "subject": "web-write-api-r24",
  "time": {
    "observed": "2026-10-19T07:48:30+00:00",
    "recorded": "2026-10-19T07:48:30+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_______________________________ test_r24_signer ________________________________

store = PosixPath('/tmp/se-workflow-test-5r1zuqzh')
cli = <function cli.<locals>._run at 0x738a5243eac0>
defs = {'project:active-goal': {'id': 'project:active-goal', 'name': 'active-goal', 'namespace': 'project', 'experimental': F....}, 'project:phase': {'id': 'project:phase', 'name': 'phase', 'namespace': 'project', 'experimental': False, ...}, ...}
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x738a52431cd0>

    def test_r24_signer(store, cli, defs, monkeypatch):
        monkeypatch.setenv("SE_WORKFLOW_SIGNED_BY", "oracle-signer")
        assert dismiss_module.default_signer() == "oracle-signer"
        _seed(cli, defs)
        check = _model_item(_snapshot(artifact_store.resolve(store)), "unsigned-check")
        original = dismiss_module.dismiss_item
        calls = []

        def spy(target, item, *, signer=None, action=None, note=None):
            calls.append({"item": item, "action": action, "signer": signer})
            return original(target, item, signer=signer, action=action, note=note)

        monkeypatch.setattr(dismiss_module, "dismiss_item", spy)
        with _running(store) as (base, _target):
            page = _page_needs(_get_json(base, "/api/snapshot"), "unsigned-check")
            assert page["revision"] == check.revision
            status = _post(base, "/api/needs", {
                "id": page["id"], "action": "sign", "revision": page["revision"], "signer": "intruder",
            })
>       assert 200 <= status < 300, status
E       AssertionError: 500
E       assert 500 < 300

tests/test_web_dashboard.py:329: AssertionError
----------------------------- Captured stderr call -----------------------------
127.0.0.1 - "GET /api/snapshot HTTP/1.1" 200 -
127.0.0.1 - "POST /api/needs HTTP/1.1" 500 -
=========================== short test summary info ============================
FAILED tests/test_web_dashboard.py::test_r24_signer - AssertionError: 500
1 failed in 4.11s
