---
{
  "base_kind": "event",
  "id": "rec-b2eaee7a-30c3-4d8f-888a-16ba4df1fa4d",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-affed3b8-e9b0-41fa-b2d9-750e40282d87",
    "diff_sha256": "e9e01e8537198af5905f71af47d8fb7a387135605d0dfd09f09161204cdae718",
    "duration_s": 0.531156,
    "effort": "library-boundary",
    "exit_code": 1,
    "failing_node_ids": "[\"tests/test_store_client_layout.py::test_store_client_layout_allows_library_and_record_types\"]",
    "method": "tdd",
    "output_sha256": "1c8d6d54fcaf7480a03e84d0762585a1f7d02f87dd8724cc10a9a403fa36ace7",
    "requirement": "R6",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "store-client-layout"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-21T10:14:42+00:00",
  "relationships": {
    "informed_by": [
      "rec-affed3b8-e9b0-41fa-b2d9-750e40282d87"
    ]
  },
  "revision": "sha256:02ba6609de0eda3825521d3aa863563fcdf6a87f6240b6bde292ead1351fde15",
  "subject": "store-client-layout",
  "time": {
    "observed": "2026-10-21T10:14:42+00:00",
    "recorded": "2026-10-21T10:14:42+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
___________ test_store_client_layout_allows_library_and_record_types ___________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-169/test_store_client_layout_allow0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x74d406890e50>

    def test_store_client_layout_allows_library_and_record_types(
        tmp_path: Path, monkeypatch
    ) -> None:
        """R6: the evidence-layout test passes when affidavit imports adaptive_artifacts and names project: record types."""
        package = tmp_path / "affidavit"
        package.mkdir()
        (package / "library_client.py").write_text(_SOURCE, encoding="utf-8")
        monkeypatch.setattr(layout, "REPO_ROOT", tmp_path)
        rejected = False
        try:
            layout.test_no_store_tokens()
        except AssertionError:
            rejected = True
>       assert not rejected, (
            "tests/test_store_client_layout.py::test_store_client_layout_allows_library_and_record_types "
            "must pass when affidavit source imports adaptive_artifacts and names project: record types"
        )
E       AssertionError: tests/test_store_client_layout.py::test_store_client_layout_allows_library_and_record_types must pass when affidavit source imports adaptive_artifacts and names project: record types
E       assert not True

tests/test_store_client_layout.py:36: AssertionError
=========================== short test summary info ============================
FAILED tests/test_store_client_layout.py::test_store_client_layout_allows_library_and_record_types
1 failed in 0.04s
