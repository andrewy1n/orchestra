---
{
  "id": "rec-0e7b2ecf-4181-4ddc-b346-0bc5da3e9e0d",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-a2fa3de2-0c6d-419c-b028-26351fdbc11a",
    "duration_s": 0.738973,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_close_batch.py::test_claim_gate_refuses_done_when_aff_verdict_nonzero"
    ],
    "informed_by": [
      "rec-a2fa3de2-0c6d-419c-b028-26351fdbc11a",
      "rec-269eeec8-e617-46f5-a7ba-a64f663406b5"
    ],
    "method": "tdd",
    "output_sha256": "5e6b273b6aabf53da0b2d077c2b6978ddcbbf1322015797907838f011d38b059",
    "requirement": "R5",
    "result": "fail",
    "revision": "61b77e4f1958556f05a740269859441df8726e10",
    "runner": "orchestra",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "claim-gate-close"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-21T06:51:21+00:00",
  "relationships": {},
  "revision": "sha256:a9169f4396f3745548cd8b91f33a272d0fc543eae084f36ba372d2c71de39222",
  "subject": "claim-gate-close",
  "time": {
    "observed": "2026-10-21T06:51:21+00:00",
    "recorded": "2026-10-21T06:51:21+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
____________ test_claim_gate_refuses_done_when_aff_verdict_nonzero _____________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-25/test_claim_gate_refuses_done_w0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x70118779de10>

    def test_claim_gate_refuses_done_when_aff_verdict_nonzero(tmp_path, monkeypatch):
        """R5: manifest claim requires aff verdict exit 0 at close revision."""
        repo, _sha = _oracle_repo(tmp_path)
        _write_manifest_claim(repo)
        bin_dir = _fake_aff_bin(tmp_path, verdict_code=1, recheck_code=0)
        monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")

        request = _claim_gate_check_request()
        with pytest.raises(close_batch.CloseRefused) as excinfo:
            _build(
                request,
                cwd=repo,
                load_acceptance=lambda _aid: _claim_gate_acceptance(),
            )
        msg = str(excinfo.value).lower()
>       assert "verdict" in msg or CLAIM_ID in msg
E       assert ('verdict' in "criterion 'rec-ac1': check-run is not runner-produced (runner must be 'orchestra', got 'aff')" or 'claim-widget' in "criterion 'rec-ac1': check-run is not runner-produced (runner must be 'orchestra', got 'aff')")

tests/test_close_batch.py:1687: AssertionError
=========================== short test summary info ============================
FAILED tests/test_close_batch.py::test_claim_gate_refuses_done_when_aff_verdict_nonzero
1 failed in 0.17s
