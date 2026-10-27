---
{
  "id": "rec-93bc5ec4-3fbd-4b7b-bec2-1c87662c54be",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-ca86ff79-3d6b-4441-91b8-e3e0abd9cdfa",
    "duration_s": 2.41351,
    "effort": "evidence-layer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_verdict.py::test_verdict_unstable_when_confirmation_disagrees",
      "tests/test_verdict.py::test_verdict_skips_confirmation_on_failed_claim"
    ],
    "informed_by": [
      "rec-ca86ff79-3d6b-4441-91b8-e3e0abd9cdfa"
    ],
    "method": "tdd",
    "output_sha256": "0fbe8b73cff8a798cc26b6c7b2676cbaa44037d439848cdd8b6c1b85122ac500",
    "requirement": "R4",
    "result": "fail",
    "revision": "7a3dd0a507dd61c7137957b1e1a4bc3e7a26e42d",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "verdict-through-runner-unstable"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-18T00:03:30+00:00",
  "relationships": {},
  "revision": "sha256:7a36b519ad5ee2bb36479dcab2aee12fd52df822df9b2e6fed7376e75a1e2e71",
  "subject": "verdict-through-runner-unstable",
  "time": {
    "observed": "2026-10-18T00:03:30+00:00",
    "recorded": "2026-10-18T00:03:30+00:00"
  }
}
---

FF                                                                       [100%]
=================================== FAILURES ===================================
______________ test_verdict_unstable_when_confirmation_disagrees _______________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-47/test_verdict_unstable_when_con0')

    def test_verdict_unstable_when_confirmation_disagrees(tmp_path: Path) -> None:
        root = tmp_path / "repo"
        log_path = tmp_path / "invocations.jsonl"
        base, head = _fixture_repo(
            root,
            log_path,
            base_behavior="flake",
            head_behavior="pass",
            base_app=b"",
            head_app=b"",
        )
        proc = _run(root, head, base)
        assert proc.returncode != 0, proc.stdout + proc.stderr
        payload = _payload(proc)
>       assert payload["result"] == "unstable"
E       AssertionError: assert 'fail' == 'unstable'
E
E         - unstable
E         + fail

tests/test_verdict.py:615: AssertionError
_______________ test_verdict_skips_confirmation_on_failed_claim ________________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-47/test_verdict_skips_confirmatio0')

    def test_verdict_skips_confirmation_on_failed_claim(tmp_path: Path) -> None:
        root = tmp_path / "repo"
        log_path = tmp_path / "invocations.jsonl"
        base, head = _fixture_repo(
            root,
            log_path,
            base_behavior="error",
            head_behavior="pass",
            base_app=b"",
            head_app=b"",
        )
        proc = _run(root, head, base)
        assert proc.returncode != 0, proc.stdout + proc.stderr
        payload = _payload(proc)
        assert payload["result"] == "fail"
        assert payload["claims"] == [{"id": CLAIM, "result": "fail", "reason": "not assertion"}]
        rows = [row for row in _read_log(log_path) if NODE in row["ids"]]
        base_rows = [row for row in rows if row["behavior"] == "error"]
>       assert base_rows == [
            {"n": 1, "behavior": "error", "ids": [NODE], "wrote": "error"}
        ]
E       AssertionError: assert [] == [{'behavior':...te': 'error'}]
E
E         Right contains one more item: {'behavior': 'error', 'ids': ['tests/test_widget.py::test_widget'], 'n': 1, 'wrote': 'error'}
E         Use -v to get more diff

tests/test_verdict.py:646: AssertionError
=========================== short test summary info ============================
FAILED tests/test_verdict.py::test_verdict_unstable_when_confirmation_disagrees
FAILED tests/test_verdict.py::test_verdict_skips_confirmation_on_failed_claim
2 failed, 14 deselected in 1.98s
