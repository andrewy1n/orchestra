---
{
  "id": "rec-9efecf5d-bdd4-448e-a85f-7647914db67c",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "subagent-honest-runner",
    "decisions": [
      "evidence-authority-approach",
      "runner-marker",
      "legacy-runner-stamp"
    ],
    "effort": "workflow-loop",
    "estimate_minutes": 15,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "evidence-authority",
    "requirements": [
      "R1",
      "R2",
      "R3",
      "R4"
    ],
    "size": "M",
    "title": "Stamp and accept only runner orchestra"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-10-21T06:53:31+00:00",
  "relationships": {},
  "revision": "sha256:a657dd53897af82abc68a41078b3882b1b2230c8d26b9e1f0c82199f59b80e56",
  "subject": "honest-runner-stamp"
}
---

## Description

R1: `orchestra check` writes each `project:check-run` with `payload.runner` equal to the string `orchestra`.
R2: The suite check-run writer used by `orchestra suite record` writes `payload.runner` equal to the string `orchestra`.
R3: `orchestra close-batch` treats a stored check-run as runner-produced only when `payload.runner` equals `orchestra`.
R4: `orchestra close-batch` refuses a stored check-run whose `payload.runner` equals `aff` as not runner-produced.

## Approach

Change the shared runner constant in `orchestra/check.py` (imported by suite) and `RUNNER_MARKER` in `orchestra/close_batch.py` from `aff` to `orchestra`. Update unit/integration tests that assert the old stamp (close_batch, check, tiered verification). Ensure a fixture stamped `aff` is refused at close and an otherwise identical `orchestra` stamp is accepted for runner matching.
