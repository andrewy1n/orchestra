---
{
  "id": "rec-aeeaa959-912d-4678-afad-06fad4adfa7e",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-b237467c-3a19-4dea-8b71-cd2428891409",
    "duration_s": 0.524397,
    "effort": "dashboard",
    "exit_code": 0,
    "informed_by": [
      "rec-b237467c-3a19-4dea-8b71-cd2428891409",
      "rec-7327937a-e592-4a73-a0db-56798ed5555e"
    ],
    "method": "tdd",
    "output_sha256": "c89452a16f114fdfc22c451f11bda9186fcb7da322be6a39365ec123950fcce8",
    "requirement": "R5",
    "result": "pass",
    "revision": "b14cde602e80990e5fb89451f944116050989964",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-30T01:24:37+00:00",
  "relationships": {},
  "revision": "sha256:8d019dbc963097e0fefa79edcb00a38d3791f60b9e36e347c1a163f8c08d9ae6",
  "subject": "verify-web-packaging-r5"
}
---

.                                                                        [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/fastapi/testclient.py:1
  /home/andrewyin/orchestra/.worktrees/web-packaging/.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1 passed, 1 warning in 0.26s
