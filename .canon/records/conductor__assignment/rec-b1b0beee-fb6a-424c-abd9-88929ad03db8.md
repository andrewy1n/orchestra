---
{
  "id": "rec-b1b0beee-fb6a-424c-abd9-88929ad03db8",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "library-boundary",
    "executor": "verify-declared-install",
    "work_item": "verify-declared-install"
  },
  "provenance": {
    "sources": [
      "verify-declared-install"
    ]
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-22T07:19:35+00:00",
  "relationships": {},
  "revision": "sha256:669d79d4f4e442a3767dd14a7c11ad8c68652b184b8ed24d8875d980c044629b",
  "subject": "verify-declared-install",
  "time": {
    "observed": "2026-10-22T07:19:35+00:00",
    "recorded": "2026-10-22T07:19:35+00:00"
  }
}
---

## Orientation

Closing verification for declared-install. Do not edit any tree. Do not take a task branch. Do not call adaptive-artifacts. Do not write .artifacts.

Write root: `/home/andrewyin/orchestra/.worktrees/declared-install` on `phase/declared-install`.

R8's command runs in `/home/andrewyin/adaptive-artifacts/.worktrees/declared-install` because that is the adaptive-artifacts checkout. Every other command runs in the orchestra phase worktree. Read only in both.

### Work-item (quote)

## Description

Prove the phase exit criteria hold together. R1–R8 in the phase specification hold. A clean install can import `adaptive_artifacts` and run `orchestra --help`. A clean install without the evidence extra cannot import affidavit. A store with format `adaptive-artifacts/project-design@0.0.0` fails to open.

## Approach

Run the integration install through `orchestra install` in a clean virtualenv, then `orchestra --help`, the affidavit absence check, the format rejection, and the declaration and import-path checks. Do not edit product code. Do not take a task branch. Use the orchestra phase worktree.

### Requirements (quote by id)

R1: The affidavit package declares a dependency on adaptive-artifacts.
R2: The orchestra package declares a dependency on adaptive-artifacts.
R3: The orchestra package does not declare affidavit as a required dependency.
R4: The orchestra `evidence` extra declares a dependency on affidavit.
R5: `orchestra install` into a clean environment leaves that environment able to import `adaptive_artifacts`.
R6: `orchestra install` into a clean environment without the evidence extra does not install affidavit.
R7: With `ADAPTIVE_ARTIFACTS_BIN` unset, orchestra opens the store by importing the library.
R8: `open_store` raises when the contract `format` is not a format this build lists as supported.

### Design / decisions (quote)

## Invariants

Importable adaptive-artifacts after a normal install. No affidavit unless the extra was requested. Unknown contract format fails open.

## Assumptions

Plugin hosts can run a package installer. `uv tool install` honors the dependency and the extra.

install-graph: dependencies-and-path
version-check: dependency-specifier-and-contract-format
dependency-direction: affidavit-on-aa-orchestra-on-both
