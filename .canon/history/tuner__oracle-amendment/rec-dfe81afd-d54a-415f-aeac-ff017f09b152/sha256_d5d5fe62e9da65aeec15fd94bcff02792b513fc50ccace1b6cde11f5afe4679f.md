---
{
  "id": "rec-dfe81afd-d54a-415f-aeac-ff017f09b152",
  "lifecycle_state": "active",
  "payload": {
    "acceptance": "rec-af80005c-c965-4740-b41e-08a8d9fd94a9",
    "effort": "workflow-loop",
    "new_hashes": [
      "tests/test_close_batch.py:sha256:7c3e4fb8bce676e86467458df4f8340c842dce44257db576ddb45c5ebc3c67be"
    ],
    "old_hashes": [
      "tests/test_close_batch.py:sha256:49f1c79e817a0c5da733e9e23904fae945b2cf96a2956662179a305578f9b8ff"
    ],
    "phase": "evidence-authority",
    "status": "approved"
  },
  "record_type": "tuner:oracle-amendment",
  "recorded_at": "2026-10-21T06:53:25+00:00",
  "relationships": {},
  "revision": "sha256:d5d5fe62e9da65aeec15fd94bcff02792b513fc50ccace1b6cde11f5afe4679f",
  "subject": "oracle-red-cli-surface-invoke",
  "time": {
    "as_of": "2026-10-21T06:53:25+00:00"
  }
}
---

## Reason

After RUNNER_MARKER flipped to orchestra, claim-gate and oracle-red acceptances could not reach their gates while the frozen helper still defaulted RUNNER to aff. Parent ratifies a one-line helper stamp flip. payload.acceptance is the acceptance record id so close-batch hash-drift matching works.

## Change

In tests/test_close_batch.py set module helper RUNNER from "aff" to "orchestra".
