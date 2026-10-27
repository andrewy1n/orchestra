---
{
  "id": "rec-ca746c0a-ea3f-478e-b1d3-3b21a0d3fc9b",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-7b352367-9ce2-4514-a6f6-674073d920e4",
    "diff_sha256": "e9e01e8537198af5905f71af47d8fb7a387135605d0dfd09f09161204cdae718",
    "duration_s": 0.564563,
    "effort": "library-boundary",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_store_client.py::test_store_client_list_bindings"
    ],
    "informed_by": [
      "rec-7b352367-9ce2-4514-a6f6-674073d920e4"
    ],
    "method": "tdd",
    "output_sha256": "7da7ce16d9b031ddf7e25ca32695b8353a4c63701faac9528d763fa39917217e",
    "requirement": "R4",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "store-client-binding-list"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-21T10:10:59+00:00",
  "relationships": {},
  "revision": "sha256:50217461e7a9fdf775751edaccc471e568e730b603bd01d3852844ff4320cd33",
  "subject": "store-client-binding-list",
  "time": {
    "observed": "2026-10-21T10:10:59+00:00",
    "recorded": "2026-10-21T10:10:59+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_______________________ test_store_client_list_bindings ________________________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-163/test_store_client_list_binding0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7ffae0ca4cd0>

    def test_store_client_list_bindings(tmp_path: Path, monkeypatch) -> None:
        """R4: affidavit.binding lists evidence-bindings by calling Project.list."""
        root = _usable_root(tmp_path)
        _creates, lists = _install_project_spy(monkeypatch)
        _block_cli(monkeypatch, binding, observation)
        result, error = _call(lambda: binding.list_bindings(root))
>       assert BIND_TYPE in lists, (
            "affidavit.binding lists evidence-bindings by calling Project.list"
        )
E       AssertionError: affidavit.binding lists evidence-bindings by calling Project.list
E       assert 'project:evidence-binding' in []

tests/test_store_client.py:220: AssertionError
=========================== short test summary info ============================
FAILED tests/test_store_client.py::test_store_client_list_bindings - Assertio...
1 failed in 0.05s
