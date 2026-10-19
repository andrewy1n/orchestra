---
{
  "base_kind": "event",
  "id": "rec-2b894e41-e3ec-4ceb-b87d-ff1946dd257f",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-07249524-c6b9-49bf-8823-074594abbd01",
    "diff_sha256": "dbe4d631378668406bc8bdc21c4f8c21b61333eacc665955a80a9e87b20a5b45",
    "duration_s": 0.818032,
    "effort": "workflow-loop",
    "exit_code": 2,
    "method": "check",
    "output_sha256": "fc647d585e29466b90a6788dc55c9b636cbe959b3dbf58f5980485a3ba28a4c4",
    "requirement": "R6",
    "result": "fail",
    "revision": "dirty",
    "runner": "se-workflow",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "verify-tiered-verification-surfaces"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-11T09:44:11+00:00",
  "relationships": {
    "informed_by": [
      "rec-07249524-c6b9-49bf-8823-074594abbd01",
      "rec-01506d98-f3b3-41af-b410-b9eaf9196043"
    ]
  },
  "revision": "sha256:cb6a769531a091185d825e83b464daff0049e1f010388f4945fef974742a0cf3",
  "subject": "verify-tiered-verification-surfaces",
  "time": {
    "observed": "2026-10-11T09:44:11+00:00",
    "recorded": "2026-10-11T09:44:11+00:00"
  }
}
---

==================================== ERRORS ====================================
_________________ ERROR collecting tests/test_dashboard_app.py _________________
tests/test_dashboard_app.py:34: in <module>
    from test_dashboard_model import (  # noqa: E402
<frozen importlib._bootstrap>:1360: in _find_and_load
    ???
<frozen importlib._bootstrap>:1331: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:935: in _load_unlocked
    ???
../.cache/uv/archive-v0/yY3yLrLD288dJfi37gLqM/lib/python3.13/site-packages/_pytest/assertion/rewrite.py:188: in exec_module
    exec(co, module.__dict__)
tests/test_dashboard_model.py:2191: in <module>
    assert False, "intentional red"
E   AssertionError: intentional red
E   assert False
________________ ERROR collecting tests/test_dashboard_model.py ________________
tests/test_dashboard_model.py:2191: in <module>
    assert False, "intentional red"
E   AssertionError: intentional red
E   assert False
=========================== short test summary info ============================
ERROR tests/test_dashboard_app.py - AssertionError: intentional red
ERROR tests/test_dashboard_model.py - AssertionError: intentional red
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
2 errors in 0.58s
