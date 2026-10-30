---
{
  "id": "rec-e14da1d5-5efb-4d5f-85af-d0a46bef98b9",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "web-packaging-suite",
    "duration_s": 45.61751,
    "effort": "dashboard",
    "evidence_kind": "integration",
    "exit_code": 0,
    "method": "check",
    "output_sha256": "849a34b44c9d407bffd67e1f65507abbac72e8b3be9f1d9996e1c6bef81a09c8",
    "result": "pass",
    "revision": "b14cde602e80990e5fb89451f944116050989964",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-30T01:28:43+00:00",
  "relationships": {},
  "revision": "sha256:b2b2796b24d09355e9692bd3a33a8c6f1ba845047245c31cef49f89bd94feb82",
  "subject": "web-packaging-suite"
}
---

bringing up nodes...
bringing up nodes...

........................................................................ [ 26%]
........................................................................ [ 53%]
........................................................................ [ 80%]
....................................................                     [100%]
=============================== warnings summary ===============================
tests/canon/test_record_file.py::test_second_writer_fails_fast_while_first_holds_the_lock
  /home/andrewyin/.local/share/uv/python/cpython-3.13.3-linux-x86_64-gnu/lib/python3.13/multiprocessing/popen_fork.py:67: DeprecationWarning: This process (pid=2128600) is multi-threaded, use of fork() may lead to deadlocks in the child.
    self.pid = os.fork()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
268 passed, 1 warning in 5.10s
bringing up nodes...
bringing up nodes...

........................................................................ [ 53%]
..............................................................           [100%]
134 passed in 7.23s
bringing up nodes...
bringing up nodes...

........................................................................ [  5%]
........................................................................ [ 11%]
........................................................................ [ 16%]
........................................................................ [ 22%]
........................................................................ [ 28%]
........................................................................ [ 33%]
........................................................................ [ 39%]
........................................................................ [ 44%]
........................................................................ [ 50%]
........................................................................ [ 56%]
........................................................................ [ 61%]
........................................................................ [ 67%]
........................................................................ [ 72%]
........................................................................ [ 78%]
........................................................................ [ 84%]
........................................................................ [ 89%]
........................................................................ [ 95%]
.............................................................            [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: 24 warnings
  /home/andrewyin/orchestra/.worktrees/web-packaging/.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1285 passed, 24 warnings in 66.87s (0:01:06)
