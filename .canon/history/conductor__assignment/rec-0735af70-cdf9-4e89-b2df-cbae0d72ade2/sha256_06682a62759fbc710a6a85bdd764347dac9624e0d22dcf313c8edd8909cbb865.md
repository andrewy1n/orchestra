---
{
  "id": "rec-0735af70-cdf9-4e89-b2df-cbae0d72ade2",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "library-boundary",
    "executor": "verify-library-e2e",
    "work_item": "verify-library-e2e"
  },
  "provenance": {
    "sources": [
      "verify-library-e2e"
    ]
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-21T12:15:45+00:00",
  "relationships": {},
  "revision": "sha256:06682a62759fbc710a6a85bdd764347dac9624e0d22dcf313c8edd8909cbb865",
  "subject": "verify-library-e2e",
  "time": {
    "observed": "2026-10-21T12:15:45+00:00",
    "recorded": "2026-10-21T12:15:45+00:00"
  }
}
---

## Orientation

Write root: `/home/andrewyin/orchestra/.worktrees/library-e2e` on `phase/library-e2e`. Do not edit the tree and do not open a task branch.

### Work-item (quote)

## Description

Prove the phase exit criteria hold together. R4: `adaptive-artifacts create` writes a record into the store `open_store` opens. R5: `orchestra close-batch` exits 0 for a close that meets the claim gate. R6: the Python close does not start `aff` or `adaptive-artifacts`.

## Approach

Run the integration test in the phase worktree. Do not edit the tree and do not open a task branch. The test runs the real `adaptive-artifacts` and `orchestra close-batch` commands, then the Python close.

### Requirements (quote by id)

R4: `adaptive-artifacts create` run in that repository writes a record into the store `open_store` opens for it.
R5: `orchestra close-batch` run as a command in that repository exits 0 for a close that meets the claim gate.
R6: The Python close function on that repository does not start a process for `aff` or `adaptive-artifacts`.

### Design / decisions (quote)

## Invariants

Command close and Python close both accept the fixture. The in-process close does not spawn the other commands.

## Assumptions

The three packages are installed in the test environment. Claim-gate behavior follows whatever `claim-clocks` has specified by the time this test is written; until then the test uses the gate `orchestra-callers` left in place.

e2e-temp-repo: generated-temp-repo
call-style: python-imports-libraries
