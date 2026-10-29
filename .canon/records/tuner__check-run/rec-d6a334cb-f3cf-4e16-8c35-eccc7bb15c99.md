---
{
  "id": "rec-d6a334cb-f3cf-4e16-8c35-eccc7bb15c99",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "ci-workflow-suite",
    "duration_s": 93.245862,
    "effort": "ci",
    "evidence_kind": "integration",
    "exit_code": 0,
    "method": "check",
    "output_sha256": "9c35318b70a0b32036d9d3f816d09d84814fe0eb487b8e65a2219e7e6a51cbbf",
    "result": "pass",
    "revision": "d5d57c1dfd901456703f361fededee3e033c40fe",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T07:05:27+00:00",
  "relationships": {},
  "revision": "sha256:539de18812a35a00c30ccf92202258f8d8264ca7afc0c64b7cc8b9fe10c486dd",
  "subject": "ci-workflow-suite"
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
  /home/andrewyin/.local/share/uv/python/cpython-3.13.3-linux-x86_64-gnu/lib/python3.13/multiprocessing/popen_fork.py:67: DeprecationWarning: This process (pid=623942) is multi-threaded, use of fork() may lead to deadlocks in the child.
    self.pid = os.fork()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
268 passed, 1 warning in 5.36s
bringing up nodes...
bringing up nodes...

........................................................................ [ 53%]
..............................................................           [100%]
134 passed in 7.66s
bringing up nodes...
bringing up nodes...

........................................................................ [  4%]
........................................................................ [  9%]
........................................................................ [ 14%]
........................................................................ [ 19%]
........................................................................ [ 24%]
........................................................................ [ 29%]
........................................................................ [ 34%]
........................................................................ [ 39%]
........................................................................ [ 44%]
........................................................................ [ 49%]
........................................................................ [ 54%]
........................................................................ [ 59%]
........................................................................ [ 64%]
........................................................................ [ 69%]
........................................................................ [ 74%]
........................................................................ [ 79%]
........................................................................ [ 84%]
........................................................................ [ 89%]
........................................................................ [ 94%]
........................................................................ [ 99%]
.....                                                                    [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: 24 warnings
  /home/andrewyin/orchestra/.worktrees/ci-workflow/.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1445 passed, 24 warnings in 288.55s (0:04:48)
....................                                                     [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/fastapi/testclient.py:1
  /home/andrewyin/orchestra/.worktrees/ci-workflow/.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

tests/test_e2e_dashboard.py: 2 warnings
tests/test_tmux_integration.py: 10 warnings
  /home/andrewyin/.local/share/uv/python/cpython-3.13.3-linux-x86_64-gnu/lib/python3.13/pty.py:95: DeprecationWarning: This process (pid=671823) is multi-threaded, use of forkpty() may lead to deadlocks in the child.
    pid, fd = os.forkpty()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
20 passed, 1445 deselected, 13 warnings in 102.65s (0:01:42)
