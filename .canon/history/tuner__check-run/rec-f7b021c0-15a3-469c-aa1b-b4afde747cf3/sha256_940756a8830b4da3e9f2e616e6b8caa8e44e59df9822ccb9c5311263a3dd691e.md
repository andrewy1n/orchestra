---
{
  "id": "rec-f7b021c0-15a3-469c-aa1b-b4afde747cf3",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-431a98ec-e552-41ea-89e0-4e025422a214",
    "duration_s": 0.830743,
    "effort": "evidence-layer",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_evidence_technique_ingest.py::test_r1_audit_records_evidence_observation"
    ],
    "informed_by": [
      "rec-431a98ec-e552-41ea-89e0-4e025422a214"
    ],
    "method": "tdd",
    "output_sha256": "3f18f21d8195f68617046d2b36b8f8bce132fcc0d9a966778b09896946ef67d5",
    "requirement": "R1",
    "result": "fail",
    "revision": "b5f72e2c9bea09433b3b930ebefc80c7b026eebf",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "audit-ingest"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-18T09:57:41+00:00",
  "relationships": {},
  "revision": "sha256:940756a8830b4da3e9f2e616e6b8caa8e44e59df9822ccb9c5311263a3dd691e",
  "subject": "audit-ingest",
  "time": {
    "observed": "2026-10-18T09:57:41+00:00",
    "recorded": "2026-10-18T09:57:41+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
__________________ test_r1_audit_records_evidence_observation __________________

store = PosixPath('/tmp/se-workflow-test-1q_dwvy5')

    def test_r1_audit_records_evidence_observation(store: Path) -> None:
        """R1: aff audit with a usable store creates an audit evidence-observation."""
        base, head = _seed_subject(store, probes=False)
        before = _list_observations(store)
        proc = _audit(store, base, head)
        payload = _advisory(proc)
        assert payload["base"] == base
        assert payload["head"] == head

        created = _created(before, _list_observations(store))
        audit_rows = _of_technique(created, AUDIT_TECHNIQUE)
>       assert audit_rows, (
            f"expected at least one new {OBS_TYPE} with technique {AUDIT_TECHNIQUE!r}; "
            f"created={created}"
        )
E       AssertionError: expected at least one new project:evidence-observation with technique 'audit'; created=[]
E       assert []

tests/test_evidence_technique_ingest.py:216: AssertionError
=========================== short test summary info ============================
FAILED tests/test_evidence_technique_ingest.py::test_r1_audit_records_evidence_observation
1 failed in 0.34s
