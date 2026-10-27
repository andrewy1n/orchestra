---
{
  "id": "rec-aa27cfe4-91f6-4a9f-a659-5fbcf9dbeb4d",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-b633ae9b-ad8f-4fa8-947f-e93af2b70315",
    "diff_sha256": "3caa71c5889c42cdaa9923a5b696961967dba1d6463a515524d9a7330abb3d91",
    "duration_s": 1.598284,
    "effort": "dashboard",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_web_fastapi_writes.py::test_r1_backlog_dismiss"
    ],
    "informed_by": [
      "rec-b633ae9b-ad8f-4fa8-947f-e93af2b70315"
    ],
    "method": "tdd",
    "output_sha256": "c28ee81cde7000c9d3fef0d7116a6924e90db9359b2e6437d0058419fde1810d",
    "requirement": "R1",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "verify-web-write-body"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-20T08:41:10+00:00",
  "relationships": {},
  "revision": "sha256:128a2aedf1691e9fe5272c26ab4d6a567413aec6f83c073956934a66f1d3b9cd",
  "subject": "verify-web-write-body",
  "time": {
    "observed": "2026-10-20T08:41:10+00:00",
    "recorded": "2026-10-20T08:41:10+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
___________________________ test_r1_backlog_dismiss ____________________________

store = PosixPath('/tmp/se-workflow-test-nvr85r15')
cli = <function cli.<locals>._run at 0x72806ef13d80>
defs = {'project:active-goal': {'id': 'project:active-goal', 'name': 'active-goal', 'namespace': 'project', 'experimental': F....}, 'project:phase': {'id': 'project:phase', 'name': 'phase', 'namespace': 'project', 'experimental': False, ...}, ...}

    def test_r1_backlog_dismiss(store, cli, defs):
        _goal(cli, defs)
        h.create_generic_record(
            cli, defs, "project:backlog-item", subject="park-me",
            extra_payload={"effort": "alpha", "status": "open", "source": "chat"},
        )
        client = _client(store)
        raw = next(
            item
            for view in _snapshot(client)["efforts"]
            for item in view["backlog"]
            if item["status"] == "open"
        )
        response = client.post(
            "/api/backlog",
            json={"id": raw["id"], "action": "dismiss"},
        )
>       assert 200 <= response.status_code < 300, response.text
E       AssertionError: {"detail":[{"type":"missing","loc":["query","request"],"msg":"Field required","input":null}]}
E       assert 422 < 300
E        +  where 422 = <Response [422 Unprocessable Entity]>.status_code

tests/test_web_fastapi_writes.py:67: AssertionError
=============================== warnings summary ===============================
../../../.cache/uv/archive-v0/620WR3gVFhQ1QKgptQa3h/lib/python3.13/site-packages/fastapi/testclient.py:1
  /home/andrewyin/.cache/uv/archive-v0/620WR3gVFhQ1QKgptQa3h/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/test_web_fastapi_writes.py::test_r1_backlog_dismiss - AssertionE...
1 failed, 1 warning in 1.20s
