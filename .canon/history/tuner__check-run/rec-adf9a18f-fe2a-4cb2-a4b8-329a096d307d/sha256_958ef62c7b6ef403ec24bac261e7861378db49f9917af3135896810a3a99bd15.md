---
{
  "id": "rec-adf9a18f-fe2a-4cb2-a4b8-329a096d307d",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-b68e9c29-fb68-4565-a945-f9b7476edf1a",
    "diff_sha256": "02bd5513b0d64ff3a05f85b8a2978d65c4e823ff4ae63436048a6c686d20731c",
    "duration_s": 0.544338,
    "effort": "dashboard",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/dashboard/test_web_packaging.py::test_r8_ci_job_installs_the_browser_and_runs_the_playwright_test"
    ],
    "informed_by": [
      "rec-b68e9c29-fb68-4565-a945-f9b7476edf1a"
    ],
    "method": "tdd",
    "output_sha256": "a85882e2f78fac0fe7e528289154c86188580587861ddccde997f89b5b74e9d5",
    "requirement": "R8",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-30T01:03:39+00:00",
  "relationships": {},
  "revision": "sha256:958ef62c7b6ef403ec24bac261e7861378db49f9917af3135896810a3a99bd15",
  "subject": "playwright-e2e-ci"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_______ test_r8_ci_job_installs_the_browser_and_runs_the_playwright_test _______

    def test_r8_ci_job_installs_the_browser_and_runs_the_playwright_test():
        names = [name for name in _jobs() if "e2e" in name]
>       assert names, "no job with e2e in its key"
E       AssertionError: no job with e2e in its key
E       assert []

tests/dashboard/test_web_packaging.py:216: AssertionError
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/fastapi/testclient.py:1
  /home/andrewyin/orchestra/.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/dashboard/test_web_packaging.py::test_r8_ci_job_installs_the_browser_and_runs_the_playwright_test
1 failed, 1 warning in 0.28s
