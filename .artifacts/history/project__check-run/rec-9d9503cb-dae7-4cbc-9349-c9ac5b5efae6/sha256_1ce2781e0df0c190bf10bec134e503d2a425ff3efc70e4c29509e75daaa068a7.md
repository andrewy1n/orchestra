---
{
  "base_kind": "event",
  "id": "rec-9d9503cb-dae7-4cbc-9349-c9ac5b5efae6",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-c07ba87d-fac0-453e-9d85-5633e2d11198",
    "diff_sha256": "5a9cec04e110c03a109863b96b20a53e06ea970cea55e3f6c167c3006a9d8601",
    "duration_s": 0.416645,
    "effort": "dashboard",
    "exit_code": 1,
    "failing_node_ids": "[\"tests/test_web_dashboard_launch.py::test_r2_same_store\"]",
    "method": "tdd",
    "output_sha256": "a237338d7f38b29c79bf4af0888d36b890534be4aa0cde9c34ec50d7557be793",
    "requirement": "R2",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "web-launcher-r2"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-19T06:37:03+00:00",
  "relationships": {
    "informed_by": [
      "rec-c07ba87d-fac0-453e-9d85-5633e2d11198"
    ]
  },
  "revision": "sha256:1ce2781e0df0c190bf10bec134e503d2a425ff3efc70e4c29509e75daaa068a7",
  "subject": "web-launcher-r2",
  "time": {
    "observed": "2026-10-19T06:37:03+00:00",
    "recorded": "2026-10-19T06:37:03+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
______________________________ test_r2_same_store ______________________________

store = PosixPath('/tmp/se-workflow-test-phrzts7h')
cli = <function cli.<locals>._run at 0x716f262c3ec0>
resolved_contract = {'format': 'adaptive-artifacts/resolved-contract@0.3.0', 'project': 'orchestra', 'resolution': {'catalog_version': '0....oken', 'multi_record_write': 'non_transactional', ...}, 'baseline_required': ['stable_ids', 'read', 'list'], ...}, ...}
tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-259/test_r2_same_store0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x716f262c5350>

    def test_r2_same_store(store, cli, resolved_contract, tmp_path, monkeypatch):
>       assert SCRIPT.is_file(), f"web launcher missing: {SCRIPT}"
E       AssertionError: web launcher missing: /home/andrewyin/orchestra/dashboard/bin/web
E       assert False
E        +  where False = is_file()
E        +    where is_file = PosixPath('/home/andrewyin/orchestra/dashboard/bin/web').is_file

tests/test_web_dashboard_launch.py:211: AssertionError
=========================== short test summary info ============================
FAILED tests/test_web_dashboard_launch.py::test_r2_same_store - AssertionErro...
1 failed in 0.24s
