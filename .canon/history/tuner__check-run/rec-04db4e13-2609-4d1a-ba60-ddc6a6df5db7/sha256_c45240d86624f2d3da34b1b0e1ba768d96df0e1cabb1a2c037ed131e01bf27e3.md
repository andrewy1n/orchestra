---
{
  "id": "rec-04db4e13-2609-4d1a-ba60-ddc6a6df5db7",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-f2749384-2dea-45ae-9083-37956aa54c4a",
    "duration_s": 0.520705,
    "effort": "dashboard",
    "exit_code": 0,
    "informed_by": [
      "rec-f2749384-2dea-45ae-9083-37956aa54c4a"
    ],
    "method": "tdd",
    "output_sha256": "0e1fc2a017af1932ddf26ac00e4fc4e59945c01b221be871ee0b8ff9407a434c",
    "requirement": "R7",
    "result": "pass",
    "revision": "b14cde602e80990e5fb89451f944116050989964",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-30T01:26:20+00:00",
  "relationships": {},
  "revision": "sha256:c45240d86624f2d3da34b1b0e1ba768d96df0e1cabb1a2c037ed131e01bf27e3",
  "subject": "playwright-e2e-seeded"
}
---

.                                                                        [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/fastapi/testclient.py:1
  /home/andrewyin/orchestra/.worktrees/web-packaging/.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1 passed, 1 warning in 0.24s
