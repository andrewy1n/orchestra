---
{
  "id": "rec-d19132f1-cbef-4f1a-a7b6-d005d982a1ca",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "hook-context-budget-suite",
    "duration_s": 55.575565,
    "effort": "session-handoff",
    "evidence_kind": "integration",
    "exit_code": 0,
    "method": "check",
    "output_sha256": "98f5537bbfc9454f363d365272ae372a19974e247439636726f2015b02c4ed36",
    "result": "pass",
    "revision": "b58320f64829ef3228e6685f6acf1551785ca46c",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T09:25:19+00:00",
  "relationships": {},
  "revision": "sha256:5919604e3e08cbb9d217aebe3d84f424ef24c141046982fce3a8f86f8d4e94ea",
  "subject": "hook-context-budget-suite"
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
  /home/andrewyin/.local/share/uv/python/cpython-3.13.3-linux-x86_64-gnu/lib/python3.13/multiprocessing/popen_fork.py:67: DeprecationWarning: This process (pid=1710340) is multi-threaded, use of fork() may lead to deadlocks in the child.
    self.pid = os.fork()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
268 passed, 1 warning in 4.91s
bringing up nodes...
bringing up nodes...

........................................................................ [ 53%]
..............................................................           [100%]
134 passed in 7.81s
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
........................................................................ [ 68%]
........................................................................ [ 73%]
........................................................................ [ 78%]
........................................................................ [ 83%]
........................................................................ [ 88%]
........................................................................ [ 93%]
........................................................................ [ 98%]
.....................                                                    [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: 24 warnings
  /home/andrewyin/orchestra/.worktrees/hook-context-budget/.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1461 passed, 24 warnings in 154.89s (0:02:34)
....................                                                     [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/fastapi/testclient.py:1
  /home/andrewyin/orchestra/.worktrees/hook-context-budget/.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

tests/test_e2e_dashboard.py: 2 warnings
tests/test_tmux_integration.py: 10 warnings
  /home/andrewyin/.local/share/uv/python/cpython-3.13.3-linux-x86_64-gnu/lib/python3.13/pty.py:95: DeprecationWarning: This process (pid=1751418) is multi-threaded, use of forkpty() may lead to deadlocks in the child.
    pid, fd = os.forkpty()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
20 passed, 1461 deselected, 13 warnings in 101.17s (0:01:41)
