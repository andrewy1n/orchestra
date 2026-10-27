---
{
  "id": "rec-7c98dc9c-21d5-481b-9ddf-6fa6fd38e64e",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-af4de5c3-440e-4e5f-9175-039d591a6fea",
    "diff_sha256": "0530346cb9ec68affcbd14bc76b024e8c2e25a219f0848bc4d0874ec293cb5e7",
    "duration_s": 0.439424,
    "effort": "evidence-layer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_attestation.py::test_verify_rejects_wrong_commit",
      "tests/test_attestation.py::test_verify_rejects_bind_mismatch_on_manifest_hash"
    ],
    "informed_by": [
      "rec-af4de5c3-440e-4e5f-9175-039d591a6fea"
    ],
    "method": "tdd",
    "output_sha256": "6a4483d73d76da544f6089b17cfbbe5d63ebed4e4384fc38437bd31e2076e244",
    "requirement": "R3",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "attest-core-bind"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-18T03:34:01+00:00",
  "relationships": {},
  "revision": "sha256:a1a49597a4b94534ec7c4e44871b2cbecc4caaaa42544754bfcc551953563dd3",
  "subject": "attest-core-bind",
  "time": {
    "observed": "2026-10-18T03:34:01+00:00",
    "recorded": "2026-10-18T03:34:01+00:00"
  }
}
---

FF                                                                       [100%]
=================================== FAILURES ===================================
_______________________ test_verify_rejects_wrong_commit _______________________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-106/test_verify_rejects_wrong_comm0')

    def test_verify_rejects_wrong_commit(tmp_path: Path) -> None:
        """R3: a well-signed attestation for commit A fails when checked as B."""
        mod = _attestation()
>       assert mod is not None, "affidavit.attestation must exist"
E       AssertionError: affidavit.attestation must exist
E       assert None is not None

tests/test_attestation.py:163: AssertionError
______________ test_verify_rejects_bind_mismatch_on_manifest_hash ______________

tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-106/test_verify_rejects_bind_misma0')

    def test_verify_rejects_bind_mismatch_on_manifest_hash(tmp_path: Path) -> None:
        """R3: a well-signed attestation fails when the presented manifest hash differs."""
        mod = _attestation()
>       assert mod is not None, "affidavit.attestation must exist"
E       AssertionError: affidavit.attestation must exist
E       assert None is not None

tests/test_attestation.py:180: AssertionError
=========================== short test summary info ============================
FAILED tests/test_attestation.py::test_verify_rejects_wrong_commit - Assertio...
FAILED tests/test_attestation.py::test_verify_rejects_bind_mismatch_on_manifest_hash
2 failed in 0.04s
