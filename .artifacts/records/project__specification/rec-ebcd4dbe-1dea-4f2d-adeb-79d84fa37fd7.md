---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-ebcd4dbe-1dea-4f2d-adeb-79d84fa37fd7",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "effort": "library-boundary",
    "phase": "orchestra-callers",
    "requirements": "R1,R2,R3,R4,R5,R6,R7,R8,R9,R10",
    "weight": "full"
  },
  "record_type": "project:specification",
  "recorded_at": "2026-10-21T08:36:50+00:00",
  "relationships": {},
  "revision": "sha256:ee578288f2fa3c21c1995a4b5a79e5be2b6c6447140c0fa03906e71bb2e5ec97",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "orchestra-callers",
  "time": {
    "as_of": "2026-10-21T08:36:50+00:00"
  }
}
---

## Requirements

R1: Modules under `orchestra/` open the store by calling `adaptive_artifacts.project.open_store`.
R2: Modules under `dashboard/` open the store by calling `adaptive_artifacts.project.open_store`.
R3: `orchestra/aa_resolve.py` is not in the tree.
R4: `dashboard/artifact_store.py` is not in the tree.
R5: `close_batch` calls `is_assertion_level_red` and does not start `aff` for that check.
R6: `close_batch` calls `run_verdict` for a manifest claim and does not start `aff` for that check.
R7: `close_batch` calls `recheck` for a manifest claim and does not start `aff` for that check.
R8: `orchestra --help` exits 0 when affidavit is not importable.
R9: A close that needs affidavit raises an error that names affidavit when affidavit is not importable.
R10: `pyproject.toml` declares a dependency on adaptive-artifacts.

## Acceptance criteria

R1–R4: a test fails if `aa_resolve.py` or `dashboard/artifact_store.py` exists, and fails if orchestra or dashboard opens the store any other way.
R5–R7: close-batch tests spy on the affidavit functions and assert `aff` is not started.
R8: a test runs `orchestra --help` with affidavit hidden from import.
R9: a test runs a claim-backed close with affidavit hidden and asserts the error names affidavit.
R10: a test reads `pyproject.toml` and finds the adaptive-artifacts dependency.

## Constraints

Affidavit is imported only from the close path. The dashboard and orchestra both use `Project` directly. Skills keep calling commands.

## Non-goals

This phase does not change the claim-gate rules for a missing acceptance or a disagreement between verdict and recheck. That is `claim-clocks`. This phase does not change the plugin installer. That is `declared-install`.

## Invariants

`orchestra --help` does not import affidavit. Store resolution has one implementation, `open_store`.

## Assumptions

`aa-library` and `affidavit-library` are importable in the test environment. The dashboard is part of this repo and uses the orchestra package dependency.
