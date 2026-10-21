---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-4f509fdd-e727-413c-8dee-b4be19ea146b",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "decisions": "affidavit-store-client,call-style,dependency-direction,three-repos",
    "effort": "library-boundary",
    "phase": "affidavit-library"
  },
  "record_type": "project:design",
  "recorded_at": "2026-10-21T08:36:49+00:00",
  "relationships": {},
  "revision": "sha256:1d4c8409436fb972c311fd1b4bd318bc1d548f0cf97da5d470f4a25539a06bca",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "affidavit-library",
  "time": {
    "as_of": "2026-10-21T08:36:49+00:00"
  }
}
---

## Architecture

`affidavit.observation` and `affidavit.binding` import `adaptive_artifacts.project` and call `open_store`, `Project.create`, and `Project.list`. Their subprocess helpers are deleted. `affidavit.cli` stays a dispatcher over `is_assertion_level_red`, `run_verdict`, `recheck`, and the observation and binding functions. `tests/test_evidence_layout.py` no longer bans the strings `adaptive-artifacts`, `project:`, `SE_WORKFLOW_STORE`, or `store-binding.json`.

## Interfaces

Observation and binding call `open_store(cwd)` and then `Project.create` / `Project.list`. They do not grow a new public module. `run_verdict(cwd, ...)` keeps its current return value and does not take a store. `aff assertion-red` reads JSON and exits 0 or 1 from `is_assertion_level_red`.

## Decisions

- `affidavit-store-client`: swap the subprocess client for `Project`.
- `call-style`: Python imports the library; `aff` stays the command.
- `dependency-direction`: affidavit depends on adaptive-artifacts and does not import orchestra.
- `three-repos`: this phase edits the affidavit repo only.

## Invariants

Observation and binding do not spawn `adaptive-artifacts`. Verdict does not open a store to decide pass or fail.

## Assumptions

`Project.create` and `Project.list` from `aa-library` are the store surface. A missing store still means observation recording is skipped, as it is today.

## Tradeoffs

Two modules import `Project`. A later signature change touches both. There is no third module whose only job is to hide that import.

## Risks

`test_no_store_tokens` is load-bearing for several older requirements. Removing it can fail those checks until their text is updated to allow the import.
