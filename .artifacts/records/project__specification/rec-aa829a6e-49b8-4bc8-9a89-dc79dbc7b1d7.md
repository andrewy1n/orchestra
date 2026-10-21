---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-aa829a6e-49b8-4bc8-9a89-dc79dbc7b1d7",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "effort": "library-boundary",
    "phase": "library-e2e",
    "requirements": "R1,R2,R3,R4,R5,R6",
    "weight": "full"
  },
  "record_type": "project:specification",
  "recorded_at": "2026-10-21T08:36:52+00:00",
  "relationships": {},
  "revision": "sha256:2e64f518956c684bdddc012760d110bb322a9ebb55b021feb637874e2a75b7ef",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "library-e2e",
  "time": {
    "as_of": "2026-10-21T08:36:52+00:00"
  }
}
---

## Requirements

R1: The test creates a temporary git repository.
R2: That repository has an initialized local artifact store with `meta.json`.
R3: That repository has a manifest claim.
R4: `adaptive-artifacts create` run in that repository writes a record into the store `open_store` opens for it.
R5: `orchestra close-batch` run as a command in that repository exits 0 for a close that meets the claim gate.
R6: The Python close function on that repository does not start a process for `aff` or `adaptive-artifacts`.

## Acceptance criteria

R1–R6 are one orchestra integration test. It builds the temporary repository, runs the two commands, calls the Python close, and fails if that call starts either process.

## Constraints

The test lives in the orchestra repo. It uses the installed `adaptive-artifacts`, `aff`, and `orchestra` commands plus the Python close function.

## Non-goals

No checked-in fixture repository. No separate smoke test per package as a substitute for this close.

## Invariants

The command close and the Python close accept the same fixture. The Python close does not shell out to the other two packages.

## Assumptions

`aa-library`, `affidavit-library`, and `orchestra-callers` are already on main in their repos. The test environment can import all three packages and find the three commands on `PATH`.
