---
{
  "id": "rec-0859e8f9-5cbd-4a9a-b5cd-e6dd0d6b23c7",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-e0e1b4c5-1a26-4b18-ae70-ca073a90ba91",
    "duration_s": 0.835728,
    "effort": "evidence-layer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_evidence_bind.py::test_r7_fixture_bind_then_recheck_exits_zero"
    ],
    "informed_by": [
      "rec-e0e1b4c5-1a26-4b18-ae70-ca073a90ba91"
    ],
    "method": "tdd",
    "output_sha256": "3d97d1ebcefa0c980e32b3c1e87cbf0339ad5f278a99ce45ccf3eabfe2f7030e",
    "requirement": "R7",
    "result": "fail",
    "revision": "21bb6fa8337eab7e8d3a959863699c9672e1041e",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "verify-evidence-bind"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-18T09:44:54+00:00",
  "relationships": {},
  "revision": "sha256:ccdde571afd09a8296a55d0914c31f6c7049304675f1485c3aa973d2ccf0da61",
  "subject": "verify-evidence-bind",
  "time": {
    "observed": "2026-10-18T09:44:54+00:00",
    "recorded": "2026-10-18T09:44:54+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_________________ test_r7_fixture_bind_then_recheck_exits_zero _________________

store = PosixPath('/tmp/se-workflow-test-zp2mpkll')

    def test_r7_fixture_bind_then_recheck_exits_zero(store: Path) -> None:
        """R7: unbound observation, aff bind, then aff recheck exits 0 while pins hold."""
>       _bind_then_recheck(store)

tests/test_evidence_bind.py:454:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

store = PosixPath('/tmp/se-workflow-test-zp2mpkll')

    def _bind_then_recheck(store: Path) -> None:
        base, head = _seed_verdict_subject(store)
        obs = _create_observation(store, base=base, head=head)
        before = [
            row
            for row in _records(_list_typed(store, BINDING_TYPE))
            if _links(row, obs["id"], CLAIM) and _is_active(row)
        ]
        assert before == []

        bound = _bind(store, obs["id"], base, head)
>       assert bound.returncode == 0, bound.stdout + bound.stderr
E       AssertionError: usage: aff [-h]
E                    {verdict,runner-template,attest,lint,claim,freeze,audit,trail} ...
E         aff: error: argument command: invalid choice: 'bind' (choose from 'verdict', 'runner-template', 'attest', 'lint', 'claim', 'freeze', 'audit', 'trail')
E
E       assert 2 == 0
E        +  where 2 = CompletedProcess(args=['/usr/bin/python3', '/home/andrewyin/affidavit--evidence-bind/bin/aff', 'bind', '--cwd', '/tmp/...id choice: 'bind' (choose from 'verdict', 'runner-template', 'attest', 'lint', 'claim', 'freeze', 'audit', 'trail')\n").returncode

tests/test_evidence_bind.py:443: AssertionError
=========================== short test summary info ============================
FAILED tests/test_evidence_bind.py::test_r7_fixture_bind_then_recheck_exits_zero
1 failed in 0.33s
