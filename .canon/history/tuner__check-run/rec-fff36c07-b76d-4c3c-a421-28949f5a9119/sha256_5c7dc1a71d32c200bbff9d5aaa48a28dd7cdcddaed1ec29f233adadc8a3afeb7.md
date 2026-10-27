---
{
  "id": "rec-fff36c07-b76d-4c3c-a421-28949f5a9119",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-af52e6e4-1191-4b01-8d7a-637858e467b2",
    "diff_sha256": "0ec1ba2f2b461ae5761c45b60aa3aa545c748c290820178dc1d9b23c98e8097c",
    "duration_s": 0.617761,
    "effort": "library-boundary",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_open_store_format.py::test_r8_open_store_raises_for_unsupported_contract_format"
    ],
    "informed_by": [
      "rec-af52e6e4-1191-4b01-8d7a-637858e467b2"
    ],
    "method": "tdd",
    "output_sha256": "30fdbe43a8043b1fbbe4a20c28555cb9c6fa6f57834443e4a0dd47569164427b",
    "requirement": "R8",
    "result": "fail",
    "revision": "dirty",
    "runner": "orchestra",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "format-gate"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-22T06:54:24+00:00",
  "relationships": {},
  "revision": "sha256:5c7dc1a71d32c200bbff9d5aaa48a28dd7cdcddaed1ec29f233adadc8a3afeb7",
  "subject": "format-gate",
  "time": {
    "observed": "2026-10-22T06:54:24+00:00",
    "recorded": "2026-10-22T06:54:24+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
__________ test_r8_open_store_raises_for_unsupported_contract_format ___________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-254/test_r8_open_store_raises_for_0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7a3ce730de10>

    def test_r8_open_store_raises_for_unsupported_contract_format(tmp_path, monkeypatch):
        """R8: open_store raises for contract format adaptive-artifacts/project-design@0.0.0."""
        for name in (
            "ARTIFACTS_STORE",
            "GIT_DIR",
            "GIT_WORK_TREE",
            "GIT_INDEX_FILE",
            "GIT_COMMON_DIR",
            "ADAPTIVE_ARTIFACTS_READONLY",
        ):
            monkeypatch.delenv(name, raising=False)
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        repo = tmp_path / "repo"
        repo.mkdir()
        init = subprocess.run(
            ["git", "init", "-q"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        assert init.returncode == 0, init.stderr

        store = repo / ".artifacts"
        store.mkdir()
        contract_rel = ".artifacts/project-design.json"
        (repo / contract_rel).write_text(
            json.dumps({"format": _UNSUPPORTED}) + "\n",
            encoding="utf-8",
        )
        (store / "meta.json").write_text(
            json.dumps({"store_version": 1, "contract": contract_rel}) + "\n",
            encoding="utf-8",
        )

        open_store = _load_open_store()
        caught = None
        try:
            open_store(repo)
        except Exception as exc:
            caught = exc
>       assert caught is not None, (
            f"open_store did not raise for contract format {_UNSUPPORTED}"
        )
E       AssertionError: open_store did not raise for contract format adaptive-artifacts/project-design@0.0.0
E       assert None is not None

tests/test_open_store_format.py:72: AssertionError
=========================== short test summary info ============================
FAILED tests/test_open_store_format.py::test_r8_open_store_raises_for_unsupported_contract_format
1 failed in 0.05s
