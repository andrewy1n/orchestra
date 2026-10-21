---
{
  "base_kind": "event",
  "id": "rec-1cb8e54a-13ad-4c7a-a0ec-47788ced1a64",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-af80005c-c965-4740-b41e-08a8d9fd94a9",
    "diff_sha256": "51390f482d1a224a9c4dd640917fcc47d9f8a4a126bb6b9bf6b684ff7383e1af",
    "duration_s": 0.797973,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": "[\"tests/test_close_batch.py::test_oracle_backed_close_invokes_aff_cli_for_assertion_red\"]",
    "method": "tdd",
    "output_sha256": "7afeb4bcc668f5460f469883648f7c68b70152ebc67ef52d06d8376909f486e0",
    "requirement": "R9",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "oracle-red-cli-surface-invoke"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-21T06:53:28+00:00",
  "relationships": {
    "informed_by": [
      "rec-af80005c-c965-4740-b41e-08a8d9fd94a9",
      "rec-ec62c47e-092d-4eb9-b67d-2f87e1e27925"
    ]
  },
  "revision": "sha256:362b39ab5a3b47cad160d6abaa0deba8b2e8a4e6e81fabcbf11dc3d0779d3e69",
  "subject": "oracle-red-cli-surface-invoke",
  "time": {
    "observed": "2026-10-21T06:53:28+00:00",
    "recorded": "2026-10-21T06:53:28+00:00"
  }
}
---

F.                                                                       [100%]
=================================== FAILURES ===================================
__________ test_oracle_backed_close_invokes_aff_cli_for_assertion_red __________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-31/test_oracle_backed_close_invok0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7bb0e9c08790>

    def test_oracle_backed_close_invokes_aff_cli_for_assertion_red(tmp_path, monkeypatch):
        """R9: assertion-level red classification comes from an Affidavit CLI call."""
>       assert False, "forced dirty red"
E       AssertionError: forced dirty red
E       assert False

tests/test_close_batch.py:1713: AssertionError
=========================== short test summary info ============================
FAILED tests/test_close_batch.py::test_oracle_backed_close_invokes_aff_cli_for_assertion_red
1 failed, 1 passed in 0.19s
