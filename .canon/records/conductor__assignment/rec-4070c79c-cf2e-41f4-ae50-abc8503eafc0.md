---
{
  "id": "rec-4070c79c-cf2e-41f4-ae50-abc8503eafc0",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "evidence-layer",
    "executor": "binding-contract",
    "work_item": "binding-contract"
  },
  "provenance": {
    "sources": [
      "binding-contract"
    ]
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-18T09:45:10+00:00",
  "relationships": {},
  "revision": "sha256:aeb02031cc4f68b6fecb7338ebc12f1e3edfce35fc26bd230a184f2ad1bf6b7f",
  "subject": "binding-contract",
  "time": {
    "observed": "2026-10-18T09:45:10+00:00",
    "recorded": "2026-10-18T09:45:10+00:00"
  }
}
---

## Orientation

Worktree: /home/andrewyin/affidavit--evidence-bind. Edit only under that path. Do not edit .artifacts/. Do not call adaptive-artifacts. Commit on the phase branch excluding .artifacts after the change.

### Work-item (quote)

## Description

R1: The project contract defines a `project:evidence-binding` record type whose payload names an observation id, a claim id, and pin revisions (base and head).

## Approach

1. Edit `contract/project-design.json` only: add a `records` entry `evidence-binding` with a supersedeable pattern (prefer `current-status`), purpose/canonical_for for an observation earning a claim under pins, required payload at least `observation_id`, `claim_id`, `base_rev`, `head_rev`. Optional payload may include `effort`.
2. Do not edit `.artifacts/project-design.json` by hand; resolve via the same path tests use when needed.
3. Do not edit `affidavit/`, `bin/`, or existing tests. Oracle tests own the R1 assertions.

### Requirements (quote by id)

R1: The project contract defines a `project:evidence-binding` record type whose payload names an observation id, a claim id, and pin revisions (base and head).

### Design / decisions (quote)

## Invariants

- No technique auto-creates a binding on record in this phase.
- Unbound observations stay queryable.
- Bind does not rewrite observation payload to assert earn.

## Assumptions

- `evidence-interface` recorder and trail exist.
- Recheck can invoke existing judge/re-run paths under the binding's pins.

binding-record: separate project:evidence-binding plus aff bind/unbind/recheck; observations stay append-only

### Frozen oracle (do not edit)

Files listed in acceptance oracle_hashes for this task are frozen.
Do not edit them. An oracle hash or test-id change is a signed amendment in `.affidavit/manifest.json`. aff verdict accepts or rejects it. A non-zero exit means the acceptance is not done.

Frozen: tests/test_evidence_bind.py
