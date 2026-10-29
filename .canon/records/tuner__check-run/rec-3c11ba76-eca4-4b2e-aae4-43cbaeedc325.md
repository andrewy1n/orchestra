---
{
  "id": "rec-3c11ba76-eca4-4b2e-aae4-43cbaeedc325",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-a73e97bd-eaa0-4a8e-a55a-b994808bc34b",
    "duration_s": 102.173236,
    "effort": "ci",
    "exit_code": 0,
    "informed_by": [
      "rec-a73e97bd-eaa0-4a8e-a55a-b994808bc34b"
    ],
    "method": "check",
    "output_sha256": "6861c0c51ff0a4f9e38558fe6876eda3bc337851ee11747a0ecf91969542798b",
    "requirement": "R19",
    "result": "pass",
    "revision": "81446c77de1aa0c0728ac4b5b1ba14f7c8ed2ede",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T06:12:19+00:00",
  "relationships": {},
  "revision": "sha256:252864df3a13efd93e645b59670c1ef40cd50e21bd07f846512de22638bb603f",
  "subject": "verify-ci-workflow-r19"
}
---

....................                                                     [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/fastapi/testclient.py:1
  /home/andrewyin/orchestra/.worktrees/ci-workflow/.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

tests/test_e2e_dashboard.py: 2 warnings
tests/test_tmux_integration.py: 10 warnings
  /home/andrewyin/.local/share/uv/python/cpython-3.13.3-linux-x86_64-gnu/lib/python3.13/pty.py:95: DeprecationWarning: This process (pid=345360) is multi-threaded, use of forkpty() may lead to deadlocks in the child.
    pid, fd = os.forkpty()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
20 passed, 1441 deselected, 13 warnings in 101.71s (0:01:41)
