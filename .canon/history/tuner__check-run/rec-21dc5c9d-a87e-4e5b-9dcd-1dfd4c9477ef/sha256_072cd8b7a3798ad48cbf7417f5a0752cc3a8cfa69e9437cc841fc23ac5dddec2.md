---
{
  "id": "rec-21dc5c9d-a87e-4e5b-9dcd-1dfd4c9477ef",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-e6ea706e-e753-4bf3-aa06-e3dab1d43a91",
    "duration_s": 0.795809,
    "effort": "dashboard",
    "exit_code": 0,
    "informed_by": [
      "rec-e6ea706e-e753-4bf3-aa06-e3dab1d43a91",
      "rec-e29f2028-2a1b-4565-bb01-2cf844f66898"
    ],
    "method": "tdd",
    "output_sha256": "6aa706668f6994460c4234959a919238a8775e8dc028293b12922a6a231941ec",
    "requirement": "R11",
    "result": "pass",
    "revision": "c63972ccaeb7aa183f573289196241789851ec9b",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T22:36:49+00:00",
  "relationships": {},
  "revision": "sha256:072cd8b7a3798ad48cbf7417f5a0752cc3a8cfa69e9437cc841fc23ac5dddec2",
  "subject": "verify-areas-and-ideas-r11"
}
---

.                                                                        [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/fastapi/testclient.py:1
  /home/andrewyin/orchestra/.worktrees/areas-and-ideas/.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1 passed, 1 warning in 0.52s
