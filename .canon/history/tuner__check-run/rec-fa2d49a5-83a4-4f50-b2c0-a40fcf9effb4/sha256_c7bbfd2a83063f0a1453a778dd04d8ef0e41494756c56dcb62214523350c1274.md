---
{
  "id": "rec-fa2d49a5-83a4-4f50-b2c0-a40fcf9effb4",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-759a1d05-be0f-4969-8ed8-391b84568459",
    "duration_s": 5.839765,
    "effort": "ci",
    "exit_code": 0,
    "informed_by": [
      "rec-759a1d05-be0f-4969-8ed8-391b84568459"
    ],
    "method": "check",
    "output_sha256": "48bb6461c11809d2756ba422ed502638bdabdcf29d5d208840ee634ec7de4cc8",
    "requirement": "R15",
    "result": "pass",
    "revision": "6a58448cca3600bedb4a9aa486e23ae361951a97",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T05:50:46+00:00",
  "relationships": {},
  "revision": "sha256:c7bbfd2a83063f0a1453a778dd04d8ef0e41494756c56dcb62214523350c1274",
  "subject": "verify-ci-workflow-r15"
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
  /home/andrewyin/.local/share/uv/python/cpython-3.13.3-linux-x86_64-gnu/lib/python3.13/multiprocessing/popen_fork.py:67: DeprecationWarning: This process (pid=175885) is multi-threaded, use of fork() may lead to deadlocks in the child.
    self.pid = os.fork()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
268 passed, 1 warning in 5.58s
