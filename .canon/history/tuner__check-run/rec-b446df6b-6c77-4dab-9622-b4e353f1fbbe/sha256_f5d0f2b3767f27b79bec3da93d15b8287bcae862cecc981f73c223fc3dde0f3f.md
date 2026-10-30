---
{
  "id": "rec-b446df6b-6c77-4dab-9622-b4e353f1fbbe",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-39597885-3e71-4421-8720-d542a075ca70",
    "duration_s": 0.493024,
    "effort": "dashboard",
    "exit_code": 0,
    "informed_by": [
      "rec-39597885-3e71-4421-8720-d542a075ca70",
      "rec-b4cc617c-64b1-4bc6-a990-5e1b95685f6c"
    ],
    "method": "tdd",
    "output_sha256": "4cae1bc3847e5cdfe824bd7b6e4f855aae56015eb6b5db6d51731ac3c6bf30bf",
    "requirement": "R10",
    "result": "pass",
    "revision": "c63972ccaeb7aa183f573289196241789851ec9b",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T22:35:18+00:00",
  "relationships": {},
  "revision": "sha256:f5d0f2b3767f27b79bec3da93d15b8287bcae862cecc981f73c223fc3dde0f3f",
  "subject": "areas-ui-route"
}
---

.                                                                        [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/fastapi/testclient.py:1
  /home/andrewyin/orchestra/.worktrees/areas-and-ideas--areas-ui/.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1 passed, 1 warning in 0.25s
