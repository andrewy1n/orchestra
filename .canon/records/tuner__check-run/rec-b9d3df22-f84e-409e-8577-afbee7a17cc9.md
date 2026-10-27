---
{
  "id": "rec-b9d3df22-f84e-409e-8577-afbee7a17cc9",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-253cbc9c-3aa1-417e-809e-11f3ae8f76c3",
    "diff_sha256": "16f8d2f407478cd2e8a28b18034a13dd4f128abebbc5061352138270e307baa7",
    "duration_s": 0.491331,
    "effort": "evidence-layer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_claim_authoring.py::test_r3_lint_claims_reports_compound_claim"
    ],
    "informed_by": [
      "rec-253cbc9c-3aa1-417e-809e-11f3ae8f76c3"
    ],
    "method": "tdd",
    "output_sha256": "d664cc46d18bc6ae08fd82b8a6d3ef8a6fe7a9d99031b114ab905669a870e95f",
    "requirement": "R3",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "claim-cli-lint"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-18T03:52:07+00:00",
  "relationships": {},
  "revision": "sha256:098758e686b430888361e5fa5470841fccde6b9192f667fc368a400f4a94f800",
  "subject": "claim-cli-lint",
  "time": {
    "observed": "2026-10-18T03:52:07+00:00",
    "recorded": "2026-10-18T03:52:07+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
__________________ test_r3_lint_claims_reports_compound_claim __________________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-149/test_r3_lint_claims_reports_co0')

    def test_r3_lint_claims_reports_compound_claim(tmp_path):
        """R3: aff lint claims reports a compound claim and leaves an atomic claim alone."""
        _write_manifest(
            tmp_path,
            {
                "claims": [
                    {
                        "id": "claim-atomic",
                        "text": "value is one",
                        "tests": [NODE],
                        "oracle_hashes": {},
                    },
                    {
                        "id": "claim-multi",
                        "text": "value is one and the widget renders",
                        "tests": [NODE],
                        "oracle_hashes": {},
                    },
                ],
                "amendments": [],
            },
        )
        proc = _aff("lint", "claims", "--cwd", str(tmp_path))
>       assert proc.returncode == 1, proc.stdout + proc.stderr
E       AssertionError: usage: aff lint [-h] {no-assert,new-skips} ...
E         aff lint: error: argument lint_command: invalid choice: 'claims' (choose from 'no-assert', 'new-skips')
E
E       assert 2 == 1
E        +  where 2 = CompletedProcess(args=['/usr/bin/python3', '/home/andrewyin/affidavit/bin/aff', 'lint', 'claims', '--cwd', '/tmp/pytes...skips} ...\naff lint: error: argument lint_command: invalid choice: 'claims' (choose from 'no-assert', 'new-skips')\n").returncode

tests/test_claim_authoring.py:313: AssertionError
=========================== short test summary info ============================
FAILED tests/test_claim_authoring.py::test_r3_lint_claims_reports_compound_claim
1 failed in 0.07s
