---
{
  "id": "rec-bcf17c0a-aac2-455c-b8dc-e073da25737e",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-affed3b8-e9b0-41fa-b2d9-750e40282d87",
    "diff_sha256": "e9e01e8537198af5905f71af47d8fb7a387135605d0dfd09f09161204cdae718",
    "duration_s": 0.538773,
    "effort": "library-boundary",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_store_client_layout.py::test_store_client_layout_allows_library_and_record_types"
    ],
    "informed_by": [
      "rec-affed3b8-e9b0-41fa-b2d9-750e40282d87"
    ],
    "method": "tdd",
    "output_sha256": "34a121f9de33c18b19d1284664521631775dd44f1a07d8796b8249a4efb4ffe3",
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
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-21T10:11:01+00:00",
  "relationships": {},
  "revision": "sha256:dc62ce9c47d6db91c354bef050a97ed9477d1e449a63591896cd493547b635fa",
  "subject": "store-client-layout",
  "time": {
    "observed": "2026-10-21T10:11:01+00:00",
    "recorded": "2026-10-21T10:11:01+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
___________ test_store_client_layout_allows_library_and_record_types ___________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-165/test_store_client_layout_allow0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7087a2b088b0>

    def test_store_client_layout_allows_library_and_record_types(
        tmp_path: Path, monkeypatch
    ) -> None:
        """R6: the evidence-layout test passes when affidavit imports adaptive_artifacts and names project: record types."""
        package = tmp_path / "affidavit"
        package.mkdir()
        (package / "library_client.py").write_text(_SOURCE, encoding="utf-8")
        monkeypatch.setattr(layout, "REPO_ROOT", tmp_path)
>       layout.test_no_store_tokens()

tests/test_store_client_layout.py:31:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

    def test_no_store_tokens() -> None:
        hits: list[str] = []
        for path in sorted((REPO_ROOT / "affidavit").rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            for token in _STORE_TOKENS:
                if token in text:
                    hits.append(f"{path.relative_to(REPO_ROOT)} contains {token}")
>       assert hits == []
E       AssertionError: assert ['affidavit/l...ins project:'] == []
E
E         Left contains one more item: 'affidavit/library_client.py contains project:'
E         Use -v to get more diff

tests/test_evidence_layout.py:76: AssertionError
=========================== short test summary info ============================
FAILED tests/test_store_client_layout.py::test_store_client_layout_allows_library_and_record_types
1 failed in 0.04s
