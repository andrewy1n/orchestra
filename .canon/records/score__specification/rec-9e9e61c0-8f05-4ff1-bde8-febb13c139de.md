---
{
  "id": "rec-9e9e61c0-8f05-4ff1-bde8-febb13c139de",
  "lifecycle_state": "active",
  "payload": {
    "effort": "canon-db-store",
    "phase": "access-layer",
    "requirements": [
      "R1",
      "R2",
      "R3",
      "R4",
      "R5",
      "R6",
      "R7",
      "R8",
      "R9",
      "R10",
      "R11",
      "R12",
      "R13"
    ],
    "weight": "full"
  },
  "record_type": "score:specification",
  "recorded_at": "2026-10-30T08:21:24+00:00",
  "relationships": {
    "supersedes": [
      "rec-c659adbf-3972-4e97-80e8-4893324fa218"
    ]
  },
  "revision": "sha256:3ccea179efaccb24a8fbdc4ddd59bfb08c44029ee3b85815ae74ff5615fa0b42",
  "subject": "access-layer"
}
---

## Requirements

R1: `orchestra/canon/backend.py` defines a `Backend` protocol that declares every storage operation its callers use.
R2: `Store` implements `Backend` with its on-disk layout unchanged.
R3: `open_store` obtains its backend from `open_backend`.
R4: `open_backend` returns the file backend when the store config has no `backend` key.
R5: No module in `orchestra/canon/` other than the file backend builds a path under the store root.
R6: No signature in `Backend` takes or returns a file path.
R7: `orchestra init` creates the store through `open_backend`.
R8: `dashboard/backend/store.py` lists records through the `Project` API.
R9: A record reference in a derived view shows the record id with no file link.
R10: No module outside `orchestra/canon/` imports `Store`.
R11: No module outside `orchestra/canon/` opens a file under the store root.
R12: `canon list --full` on the real store prints the same output after the phase as before it.
R13: `canon validate` passes on the real store.

## Acceptance criteria

- R1, R2, R3, R4, R6: unit tests in `tests/canon` for protocol conformance, the factory and the signatures.
- R5, R10, R11: a boundary test in `tests/canon` that scans imports and path building. It passes on the final tree and fails on a seeded violation.
- R7, R8: unit tests for the init command and the dashboard store module.
- R9: `tests/test_views.py` asserts the view output has no `.canon/` link.
- R12: a script captures `canon list --full` before and after and diffs the two files (command run).
- R13: `canon validate` exits 0 (command run).

## Constraints

- The file backend's behaviour and on-disk format do not change.
- The protocol carries only operations that a caller uses today. No speculative methods.
- No new dependency.

## Non-goals

- Any SQLite code.
- Changing the file format or the op-log semantics.
- `orchestra/sessions/*` use of `~/.canon`, which looks unrelated to the repo store. Plan-phase confirms this.
- `orchestra/tuner/audit.py` path rule for `.canon/`.

## Invariants

- No method signature in `Backend` takes or returns a file path.
- Output of `canon list --full` on the real store is unchanged.

## Assumptions

- Most of the 35 importers already use `Project`. Plan-phase counts the exact `Store` users first.
- The existing 18 test files that assume the file layout keep passing against the file backend.
