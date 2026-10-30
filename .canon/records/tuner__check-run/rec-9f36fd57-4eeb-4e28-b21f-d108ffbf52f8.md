---
{
  "id": "rec-9f36fd57-4eeb-4e28-b21f-d108ffbf52f8",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-997e57be-2cfa-4b58-b911-18c12ce02a4f",
    "duration_s": 0.85665,
    "effort": "dashboard",
    "exit_code": 0,
    "informed_by": [
      "rec-997e57be-2cfa-4b58-b911-18c12ce02a4f",
      "rec-5ed6acd6-ab93-4dee-8b5c-1c58f33294db"
    ],
    "method": "tdd",
    "output_sha256": "411785fb8b3604d96b70a42e952aa7f2de21276a31cbea5de0e183805041271c",
    "requirement": "R4",
    "result": "pass",
    "revision": "faa29a369266d52e88e6b6046a4a9f979e27d41a",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T22:30:25+00:00",
  "relationships": {},
  "revision": "sha256:eca4b9277e0d9602c1eafad015b4412c3c1e8f20ca4f5222be31431661328cc4",
  "subject": "areas-endpoint-both"
}
---

.                                                                        [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/fastapi/testclient.py:1
  /home/andrewyin/orchestra/.worktrees/areas-and-ideas--areas-endpoint/.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1 passed, 1 warning in 0.60s
