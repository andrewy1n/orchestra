---
{
  "id": "rec-fbfaf22d-0ff4-40aa-b0b4-04af91618d19",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-feea1426-6af8-4732-8e6b-431eb5331240",
    "duration_s": 0.669365,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_close_batch.py::test_claim_gate_refuses_done_when_aff_recheck_nonzero"
    ],
    "informed_by": [
      "rec-feea1426-6af8-4732-8e6b-431eb5331240",
      "rec-269eeec8-e617-46f5-a7ba-a64f663406b5"
    ],
    "method": "tdd",
    "output_sha256": "f83f198f683592b9104ff180e43e38ab8a3cb417b26ff43a8acf36695f7e74a6",
    "requirement": "R6",
    "result": "fail",
    "revision": "51cd740b7588ae41ef9a50360d992d6995d1e09d",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "claim-gate-close-recheck"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-21T06:50:36+00:00",
  "relationships": {},
  "revision": "sha256:af4f0a2842bd98b70db9127d49578e7c0fcdd5d9bf0801510fb1cb15f0a86d52",
  "subject": "claim-gate-close-recheck",
  "time": {
    "observed": "2026-10-21T06:50:36+00:00",
    "recorded": "2026-10-21T06:50:36+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
____________ test_claim_gate_refuses_done_when_aff_recheck_nonzero _____________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-20/test_claim_gate_refuses_done_w0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x788b3a4999f0>

    def test_claim_gate_refuses_done_when_aff_recheck_nonzero(tmp_path, monkeypatch):
        """R6: manifest claim requires aff recheck exit 0."""
        repo, _sha = _oracle_repo(tmp_path)
        _write_manifest_claim(repo)
        bin_dir = _fake_aff_bin(tmp_path, verdict_code=0, recheck_code=1)
        monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")

        request = _claim_gate_check_request()
>       with pytest.raises(close_batch.CloseRefused) as excinfo:
E       Failed: DID NOT RAISE <class 'orchestra.close_batch.CloseRefused'>

tests/test_close_batch.py:1698: Failed
=========================== short test summary info ============================
FAILED tests/test_close_batch.py::test_claim_gate_refuses_done_when_aff_recheck_nonzero
1 failed in 0.10s
