---
{
  "id": "rec-8e1ddbb8-c263-440a-bbff-acd6809064e5",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "area-levels-suite",
    "duration_s": 8.800616,
    "effort": "dashboard",
    "evidence_kind": "integration",
    "exit_code": 0,
    "method": "check",
    "output_sha256": "c1cabb5bbafdd6f66e64e37bb042ae3415b089fbe7138806ad919fbf49e7fd49",
    "result": "pass",
    "revision": "775ca3e848e01b86c8f06d9de92d659c15c82167",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-30T09:25:46+00:00",
  "relationships": {},
  "revision": "sha256:77e89f9af80e85b50c9b8ae1f8052c80b28c3d085e1c027fd0fd788718014fe5",
  "subject": "area-levels-suite"
}
---

bringing up nodes...
bringing up nodes...

........................................................................ [ 26%]
........................................................................ [ 53%]
........................................................................ [ 80%]
.....................................................                    [100%]
=============================== warnings summary ===============================
tests/canon/test_record_file.py::test_second_writer_fails_fast_while_first_holds_the_lock
  /home/andrewyin/.local/share/uv/python/cpython-3.13.3-linux-x86_64-gnu/lib/python3.13/multiprocessing/popen_fork.py:67: DeprecationWarning: This process (pid=3193408) is multi-threaded, use of fork() may lead to deadlocks in the child.
    self.pid = os.fork()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
269 passed, 1 warning in 5.36s
bringing up nodes...
bringing up nodes...

........................................................................ [ 53%]
..............................................................           [100%]
134 passed in 8.76s
bringing up nodes...
bringing up nodes...

........................................................................ [  5%]
........................................................................ [ 10%]
........................................................................ [ 16%]
........................................................................ [ 21%]
........................................................................ [ 27%]
........................................................................ [ 32%]
........................................................................ [ 37%]
........................................................................ [ 43%]
........................................................................ [ 48%]
........................................................................ [ 54%]
........................................................................ [ 59%]
........................................................................ [ 64%]
........................................................................ [ 70%]
........................................................................ [ 75%]
........................................................................ [ 81%]
........................................................................ [ 86%]
........................................................................ [ 91%]
........................................................................ [ 97%]
...................................                                      [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: 24 warnings
  /home/andrewyin/orchestra/.worktrees/area-levels/.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1331 passed, 24 warnings in 62.09s (0:01:02)
