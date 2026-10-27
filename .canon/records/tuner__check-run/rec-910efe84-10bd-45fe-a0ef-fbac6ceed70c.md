---
{
  "id": "rec-910efe84-10bd-45fe-a0ef-fbac6ceed70c",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-7a536e2e-56fe-418d-9f76-ee4819ffc972",
    "diff_sha256": "0c9f41e15d4f22f886450999c4df60d7c964e1b781d39220b2ac9af1954ef5b7",
    "duration_s": 3.397181,
    "effort": "evidence-layer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_evidence_interface.py::test_r4_verdict_trail_and_subsequent_verdict_pass"
    ],
    "informed_by": [
      "rec-7a536e2e-56fe-418d-9f76-ee4819ffc972"
    ],
    "method": "tdd",
    "output_sha256": "b648f393d94bdedb631e25968bd6a68182f642beb826887cbb04dfd4c103ff37",
    "requirement": "R4",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "verify-evidence-interface"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-18T09:03:55+00:00",
  "relationships": {},
  "revision": "sha256:7432b594f658933d46021f1f1a54d20215f3cc97fa95dd354ca651751bd1351f",
  "subject": "verify-evidence-interface",
  "time": {
    "observed": "2026-10-18T09:03:55+00:00",
    "recorded": "2026-10-18T09:03:55+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
______________ test_r4_verdict_trail_and_subsequent_verdict_pass _______________

store = PosixPath('/tmp/se-workflow-test-9ge_2lq8')

    def test_r4_verdict_trail_and_subsequent_verdict_pass(store: Path) -> None:
        """R4 / verify-evidence-interface: verdict → trail → verdict still exits 0."""
        base, head = _seed_verdict_subject(store)
        before = _list_evidence_observations(store)

        first = _verdict(store, base, head)
        assert first.returncode == 0, first.stdout + first.stderr
        assert _payload(first)["result"] == "pass"

        after = _list_evidence_observations(store)
>       assert len(after) == len(before) + 1
E       assert 0 == (0 + 1)
E        +  where 0 = len([])
E        +  and   0 = len([])

tests/test_evidence_interface.py:266: AssertionError
=========================== short test summary info ============================
FAILED tests/test_evidence_interface.py::test_r4_verdict_trail_and_subsequent_verdict_pass
1 failed in 2.86s
