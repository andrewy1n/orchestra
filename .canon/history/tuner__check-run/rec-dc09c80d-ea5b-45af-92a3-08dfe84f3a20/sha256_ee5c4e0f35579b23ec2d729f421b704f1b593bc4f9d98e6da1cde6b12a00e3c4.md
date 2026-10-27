---
{
  "id": "rec-dc09c80d-ea5b-45af-92a3-08dfe84f3a20",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "ci-verdict-fixture-suite",
    "duration_s": 18,
    "effort": "evidence-layer",
    "evidence_kind": "integration",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/fixtures/verdict-repo/tests/test_widget.py::test_widget",
      "tests/test_claim_authoring.py::test_r2_standalone_add_freeze_verdict_passes"
    ],
    "method": "check",
    "output_sha256": "96a00b8ff29942b2705ed237546c70ac058056d57e354ccc50f2881462c4f077",
    "result": "fail",
    "revision": "65c76f72f5c5b4c12db8ed4961d8d5fb50adbdc2",
    "runner": "affidavit",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "ci-verdict-fixture-suite"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-18T06:10:08+00:00",
  "relationships": {},
  "revision": "sha256:ee5c4e0f35579b23ec2d729f421b704f1b593bc4f9d98e6da1cde6b12a00e3c4",
  "subject": "ci-verdict-fixture-suite",
  "time": {
    "observed": "2026-10-18T06:10:08+00:00",
    "recorded": "2026-10-18T06:10:08+00:00"
  }
}
---

Advisory suite (non-tmux leg) at phase head 65c76f7: 2 failed, 107 passed in 17.92s. tmux leg not run (&& short-circuit).

Failing:
- tests/fixtures/verdict-repo/tests/test_widget.py::test_widget — ModuleNotFoundError: No module named 'app' (fixture oracle collected as a normal test)
- tests/test_claim_authoring.py::test_r2_standalone_add_freeze_verdict_passes — empty JUnit ParseError under xdist (passes in isolation)

Source: advisory suite subagent evidence.
