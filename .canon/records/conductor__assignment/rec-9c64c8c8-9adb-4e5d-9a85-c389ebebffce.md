---
{
  "id": "rec-9c64c8c8-9adb-4e5d-9a85-c389ebebffce",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "workflow-loop",
    "executor": "subagent-honest-runner",
    "work_item": "honest-runner-stamp"
  },
  "provenance": {
    "sources": [
      "honest-runner-stamp"
    ]
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-21T06:39:19+00:00",
  "relationships": {},
  "revision": "sha256:63b9dba2e6ecee1faa530c9c0c80326b784d93a0b038a38e1e858f24d25f50b9",
  "subject": "honest-runner-stamp",
  "time": {
    "observed": "2026-10-21T06:39:19+00:00",
    "recorded": "2026-10-21T06:39:19+00:00"
  }
}
---

## Orientation

Territory: Orchestra worktree `/home/andrewyin/orchestra/.worktrees/evidence-authority` only.
Concurrency: Wave-1 peers also edit `orchestra/close_batch.py`. You own ONLY the runner stamp constants:
- `orchestra/check.py` `RUNNER` → `"orchestra"`
- `orchestra/close_batch.py` `RUNNER_MARKER` → `"orchestra"`
Do not add claim-gate or oracle-red CLI logic. Do not rewrite whole files — surgical constant changes.
Do not edit `.artifacts/`. Do not call `adaptive-artifacts`.
After code lands, commit on the phase branch (exclude `.artifacts`) with subject like `feat(evidence-authority): stamp runner orchestra`.

### Work-item (quote)

## Description

R1: `orchestra check` writes each `project:check-run` with `payload.runner` equal to the string `orchestra`.
R2: The suite check-run writer used by `orchestra suite record` writes `payload.runner` equal to the string `orchestra`.
R3: `orchestra close-batch` treats a stored check-run as runner-produced only when `payload.runner` equals `orchestra`.
R4: `orchestra close-batch` refuses a stored check-run whose `payload.runner` equals `aff` as not runner-produced.

## Approach

Change the shared runner constant in `orchestra/check.py` (imported by suite) and `RUNNER_MARKER` in `orchestra/close_batch.py` from `aff` to `orchestra`. Update unit/integration tests that assert the old stamp (close_batch, check, tiered verification). Ensure a fixture stamped `aff` is refused at close and an otherwise identical `orchestra` stamp is accepted for runner matching.

### Requirements (quote by id)

R1: `orchestra check` writes each `project:check-run` with `payload.runner` equal to the string `orchestra`.
R2: The suite check-run writer used by `orchestra suite record` writes `payload.runner` equal to the string `orchestra`.
R3: `orchestra close-batch` treats a stored check-run as runner-produced only when `payload.runner` equals `orchestra`.
R4: `orchestra close-batch` refuses a stored check-run whose `payload.runner` equals `aff` as not runner-produced.

### Design / decisions (quote)

## Invariants

- A typed-in check-run with `runner: "orchestra"` remains forgeable as an Orchestra operational record; Affidavit claim earning does not trust that stamp.
- Manifest claim `done` requires Affidavit CLI success, independent of the check-run stamp.
- Import direction: Orchestra → Affidavit CLI only; Affidavit does not import Orchestra.

## Assumptions

- Claim id on an acceptance (or equivalent link skills already document) is available to close-batch for the manifest gate.
- Affidavit CLI addition for assertion-level red can land in the Affidavit repo as part of this phase's delivery when Orchestra Landing needs it.

evidence-authority-approach: honest-stamp-aff-claim-gate
runner-marker: orchestra
legacy-runner-stamp: refuse-aff

### Frozen oracle (do not edit)

Files listed in acceptance oracle_hashes for this task are frozen.
Do not edit them. An oracle hash or test-id change is a signed amendment in `.affidavit/manifest.json`. aff verdict accepts or rejects it. A non-zero exit means the acceptance is not done.

Frozen paths (shared across wave-1 acceptances):
- tests/test_affidavit_check.py
- tests/test_tiered_verification.py
- tests/test_close_batch.py
- tests/test_affidavit_import_boundary.py
