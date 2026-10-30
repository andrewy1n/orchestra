---
{
  "id": "rec-54329bb0-0efc-44c3-b040-9c0c6e863da6",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-7c34dc82-8372-46fc-a324-25b8d8149c6e",
    "duration_s": 0.524853,
    "effort": "dashboard",
    "exit_code": 0,
    "informed_by": [
      "rec-7c34dc82-8372-46fc-a324-25b8d8149c6e"
    ],
    "method": "tdd",
    "output_sha256": "c89452a16f114fdfc22c451f11bda9186fcb7da322be6a39365ec123950fcce8",
    "requirement": "R6",
    "result": "pass",
    "revision": "b14cde602e80990e5fb89451f944116050989964",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-30T01:25:45+00:00",
  "relationships": {},
  "revision": "sha256:cbfdd3a5b54ccb44a5f65e05fd9ea6f0951483df5be4bd30b05a0cabb1b2d49a",
  "subject": "playwright-e2e"
}
---

.                                                                        [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/fastapi/testclient.py:1
  /home/andrewyin/orchestra/.worktrees/web-packaging/.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1 passed, 1 warning in 0.26s
