---
{
  "base_kind": "event",
  "id": "rec-c7a6acac-a090-445c-9efa-ff2f72cf3516",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-b5eb3ea3-6ec1-4431-ab56-fcb60d7b1574",
    "diff_sha256": "dbe4d631378668406bc8bdc21c4f8c21b61333eacc665955a80a9e87b20a5b45",
    "duration_s": 1.171388,
    "effort": "workflow-loop",
    "exit_code": 2,
    "method": "tdd",
    "output_sha256": "08f776fc9019e17431746cbcf387ef45670781494d1d8e6556917e90cf611368",
    "requirement": "R6",
    "result": "fail",
    "revision": "dirty",
    "runner": "se-workflow",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "tier2-dashboard"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-11T09:42:16+00:00",
  "relationships": {
    "informed_by": [
      "rec-b5eb3ea3-6ec1-4431-ab56-fcb60d7b1574",
      "rec-711fb3b5-a84a-4687-a186-74d2a127f1a7"
    ]
  },
  "revision": "sha256:8c6f8fcc4c5e9baf589c49db5e7c50585e124d7c572a82e6152fc25ed2b670bd",
  "subject": "tier2-dashboard",
  "time": {
    "observed": "2026-10-11T09:42:16+00:00",
    "recorded": "2026-10-11T09:42:16+00:00"
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
2 errors in 0.93s
