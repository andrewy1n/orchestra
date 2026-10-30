---
{
  "id": "rec-bb1af936-0e72-4ed0-abdd-f6b4670bda78",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-522d0295-4ac2-44c2-87f5-3e13aedd33a8",
    "diff_sha256": "0224ee7499e128c65cc468de42972059935286a597132b3dc2e014bd36e6a6d4",
    "duration_s": 0.537962,
    "effort": "dashboard",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/dashboard/test_web_packaging.py::test_r2_wheel_job_builds_the_frontend_before_the_smoke_script"
    ],
    "informed_by": [
      "rec-522d0295-4ac2-44c2-87f5-3e13aedd33a8"
    ],
    "method": "tdd",
    "output_sha256": "55241b52ebfaea1f054935d131937a1b065630991d24a20026fa8dc8551618fd",
    "requirement": "R2",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-30T01:03:28+00:00",
  "relationships": {},
  "revision": "sha256:994e1eb387e118d5f51226abebd7762c433c355520bdf58a9f1abd99be614a04",
  "subject": "dist-in-wheel-job"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
________ test_r2_wheel_job_builds_the_frontend_before_the_smoke_script _________

    def test_r2_wheel_job_builds_the_frontend_before_the_smoke_script():
        located = _located_lines(_job("wheel"))
        smoke = [i for i, (_, line) in enumerate(located) if line == SMOKE_LINE]
        assert smoke, "wheel job does not run the smoke script"
        builds = [
            i for i, (directory, line) in enumerate(located)
            if line == "npm run build" and directory == FRONTEND_REL
        ]
>       assert builds, f"wheel job has no `npm run build` in {FRONTEND_REL}"
E       AssertionError: wheel job has no `npm run build` in dashboard/frontend
E       assert []

tests/dashboard/test_web_packaging.py:144: AssertionError
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/fastapi/testclient.py:1
  /home/andrewyin/orchestra/.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/dashboard/test_web_packaging.py::test_r2_wheel_job_builds_the_frontend_before_the_smoke_script
1 failed, 1 warning in 0.28s
