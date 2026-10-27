---
{
  "id": "rec-212f2086-7caf-4a08-8cdd-42c4eea1400a",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-cc03c990-7e5c-4647-b54b-e1adedb8e479",
    "duration_s": 0.602761,
    "effort": "library-boundary",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_claim_clocks.py::test_claim_id_read_only_from_payload_claim"
    ],
    "informed_by": [
      "rec-cc03c990-7e5c-4647-b54b-e1adedb8e479"
    ],
    "method": "tdd",
    "output_sha256": "b27c08192c827c03b46204f106cd6606f8bf6d07dedb64280d0db134d14531e7",
    "requirement": "R1",
    "result": "fail",
    "revision": "ee99dc40a59190f169f510bb16f2f44750f63f8b",
    "runner": "orchestra",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "claim-gate-source"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-23T08:46:37+00:00",
  "relationships": {},
  "revision": "sha256:0d52b7a0f49c84979dc864a5baac43cda6aeae4d4e4c8cd6f3f14dde19eda38d",
  "subject": "claim-gate-source",
  "time": {
    "observed": "2026-10-23T08:46:37+00:00",
    "recorded": "2026-10-23T08:46:37+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
__________________ test_claim_id_read_only_from_payload_claim __________________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-5/test_claim_id_read_only_from_p0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7afa33de14e0>

    def test_claim_id_read_only_from_payload_claim(tmp_path, monkeypatch):
        """R1: a manifest claim named only by the acceptance subject is not gated."""
        repo = tmp_path / "repo"
        repo.mkdir()
        _write_manifest_claim(repo)
        verdict_calls: list[tuple] = []
        recheck_calls: list[tuple] = []

        def run_verdict(*args, **kwargs):
            verdict_calls.append((args, kwargs))
            return {"result": "fail"}

        def recheck(*args, **kwargs):
            recheck_calls.append((args, kwargs))
            return {"result": "pass"}

        _patch_affidavit(monkeypatch, "affidavit.verdict", "run_verdict", run_verdict)
        _patch_affidavit(monkeypatch, "affidavit.binding", "recheck", recheck)

        refused = _refusal(
            lambda: _build(
                _request(),
                cwd=repo,
                load_acceptance=lambda _aid: _acceptance(
                    include_claim=False, subject=CLAIM_ID
                ),
            )
        )
>       assert refused is None, (
            "a claim id read only from the acceptance subject must not gate: "
            f"{refused}"
        )
E       AssertionError: a claim id read only from the acceptance subject must not gate: affidavit verdict refused for claim 'claim-widget' at revision 'deadbeef'
E       assert CloseRefused("affidavit verdict refused for claim 'claim-widget' at revision 'deadbeef'") is None

tests/test_claim_clocks.py:189: AssertionError
=========================== short test summary info ============================
FAILED tests/test_claim_clocks.py::test_claim_id_read_only_from_payload_claim
1 failed in 0.06s
