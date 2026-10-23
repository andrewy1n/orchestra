---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-3feafbae-a124-4f65-aeb0-ae5dc1269617",
  "identity": "unknown",
  "lifecycle_state": "superseded",
  "payload": {
    "acceptance": "honest-runner-stamp-refuse-aff",
    "effort": "workflow-loop",
    "new_hashes": "tests/test_close_batch.py:sha256:7c3e4fb8bce676e86467458df4f8340c842dce44257db576ddb45c5ebc3c67be",
    "old_hashes": "tests/test_close_batch.py:sha256:49f1c79e817a0c5da733e9e23904fae945b2cf96a2956662179a305578f9b8ff",
    "phase": "evidence-authority",
    "status": "approved"
  },
  "record_type": "project:oracle-amendment",
  "recorded_at": "2026-10-23T20:15:08+00:00",
  "relationships": {},
  "revision": "sha256:8ae758d643147d4fe49b99f46f44b27eab5add99712efa275b51b13e7ae80bb7",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "honest-runner-stamp-refuse-aff",
  "time": {
    "as_of": "2026-10-21T06:49:23+00:00"
  }
}
---

## Reason

After RUNNER_MARKER flipped to orchestra, claim-gate and oracle-red acceptances could not reach their gates while the frozen helper still defaulted RUNNER to aff. Parent ratifies a one-line helper stamp flip so wave-1 closes can proceed. Close-batch still keys hash drift on project:oracle-amendment.

## Change

In tests/test_close_batch.py set module helper RUNNER from "aff" to "orchestra". R4 refuse-aff coverage still passes an explicit runner:"aff" fixture.
