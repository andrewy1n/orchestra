---
{
  "id": "rec-4c8b7ae1-dffd-4acd-90bf-2463c0c524e8",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-75798857-63f7-4bf9-ba62-1702b7d62da3",
    "diff_sha256": "04892fa8d198dd80da3c276c159d3d0c436b276b7fc38aad2fc7015a3740995c",
    "duration_s": 0.489108,
    "effort": "evidence-layer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_claim_authoring.py::test_r1_claim_add_writes_manifest_entry_standalone"
    ],
    "informed_by": [
      "rec-75798857-63f7-4bf9-ba62-1702b7d62da3"
    ],
    "method": "tdd",
    "output_sha256": "7aabb618b8625bc6efce425e15eb50606dfccc2c1dfb7c8c74c1475a0b923552",
    "requirement": "R1",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "claim-cli"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-18T03:52:04+00:00",
  "relationships": {},
  "revision": "sha256:65ad095dc5b8e507c4f7777f70a0231c068a0e15912063ae454212061028120e",
  "subject": "claim-cli",
  "time": {
    "observed": "2026-10-18T03:52:04+00:00",
    "recorded": "2026-10-18T03:52:04+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
______________ test_r1_claim_add_writes_manifest_entry_standalone ______________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-147/test_r1_claim_add_writes_manif0')

    def test_r1_claim_add_writes_manifest_entry_standalone(tmp_path):
        """R1: aff claim add appends a claim to the committed manifest format without orchestra."""
        fresh = tmp_path / "fresh"
        fresh.mkdir()
        proc = _aff(
            "claim", "add", "--cwd", str(fresh),
            "--id", "claim-a", "--text", "value is one",
            "--test", NODE, "--test", f"{ORACLE_REL}::test_other",
        )
>       assert proc.returncode == 0, proc.stderr
E       AssertionError: usage: aff [-h] {verdict,runner-template,attest,lint} ...
E         aff: error: argument command: invalid choice: 'claim' (choose from 'verdict', 'runner-template', 'attest', 'lint')
E
E       assert 2 == 0
E        +  where 2 = CompletedProcess(args=['/usr/bin/python3', '/home/andrewyin/affidavit/bin/aff', 'claim', 'add', '--cwd', '/tmp/pytest-...naff: error: argument command: invalid choice: 'claim' (choose from 'verdict', 'runner-template', 'attest', 'lint')\n").returncode

tests/test_claim_authoring.py:167: AssertionError
=========================== short test summary info ============================
FAILED tests/test_claim_authoring.py::test_r1_claim_add_writes_manifest_entry_standalone
1 failed in 0.07s
