---
{
  "id": "rec-8e9f1f73-e54b-45f8-bf73-6390a71ee4a0",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-1ef835e4-41dc-4aeb-8462-c21de870e1f1",
    "diff_sha256": "a002df4c85f5a8d80039beb5a63633106e3b514da17f598d11445ea7535bdce7",
    "duration_s": 6.130092,
    "effort": "evidence-layer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_evidence_kind.py::test_r1_manifest_claim_may_declare_evidence_kind"
    ],
    "informed_by": [
      "rec-1ef835e4-41dc-4aeb-8462-c21de870e1f1"
    ],
    "method": "tdd",
    "output_sha256": "150132f672c72a9280378f25c300d6fa351813491c0466d07b76f7ef8974e910",
    "requirement": "R1",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "kind-enforcement"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-18T03:47:43+00:00",
  "relationships": {},
  "revision": "sha256:204ad1f4e1d3560a97ddd115fa870cab0fedca945c39dfd5c48daf7dccebe09e",
  "subject": "kind-enforcement",
  "time": {
    "observed": "2026-10-18T03:47:43+00:00",
    "recorded": "2026-10-18T03:47:43+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_______________ test_r1_manifest_claim_may_declare_evidence_kind _______________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-134/test_r1_manifest_claim_may_dec0')

    def test_r1_manifest_claim_may_declare_evidence_kind(tmp_path: Path) -> None:
        """R1: A manifest claim may declare evidence_kind as unit, integration, or interaction."""
        for kind in ("unit", "integration"):
            root = tmp_path / kind
            head = _repo(root, kind)
            proc = _verdict(root, head)
            assert proc.returncode == 0, proc.stdout + proc.stderr
            assert _payload(proc)["result"] == "pass"

        root = tmp_path / "bogus"
        head = _repo(root, "bogus")
        proc = _verdict(root, head)
>       assert proc.returncode != 0, proc.stdout + proc.stderr
E       AssertionError: {"result":"pass","claims":[{"id":"claim-widget","result":"pass"}]}
E
E       assert 0 != 0
E        +  where 0 = CompletedProcess(args=['/home/andrewyin/affidavit/bin/aff', 'verdict', '--at', '380141baa7489533e4a8b2813ff733b4c4a0b0...claim-widget'], returncode=0, stdout='{"result":"pass","claims":[{"id":"claim-widget","result":"pass"}]}\n', stderr='').returncode

tests/test_evidence_kind.py:115: AssertionError
=========================== short test summary info ============================
FAILED tests/test_evidence_kind.py::test_r1_manifest_claim_may_declare_evidence_kind
1 failed in 5.69s
