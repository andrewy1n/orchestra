---
{
  "base_kind": "instruction",
  "id": "rec-daf5d122-f3af-44fb-aea9-76f6ba9895ee",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "packaging",
    "executor": "inline",
    "work_item": "shared-aa-resolver"
  },
  "provenance": {
    "sources": [
      "shared-aa-resolver"
    ]
  },
  "record_type": "project:assignment",
  "recorded_at": "2026-10-14T08:31:30+00:00",
  "relationships": {},
  "revision": "sha256:b395f83ad1d8d32fca32e20fb0f3b86508ff27d4cbfac41ed84308357adfe506",
  "subject": "shared-aa-resolver",
  "time": {
    "observed": "2026-10-14T08:31:30+00:00",
    "recorded": "2026-10-14T08:31:30+00:00"
  }
}
---

## Orientation

Worktree /home/andrewyin/se-workflow--plugin-root-and-cli. Concurrent with close-batch-cli: do not edit scripts/close_batch.py or se_workflow/cli.py. Own se_workflow/aa_resolve.py (new), se_workflow/aa.py, dashboard/artifact_store.py, tests/test_aa_resolve.py.

### Requirements
R2: `se_workflow.aa` and `dashboard.artifact_store` share one adaptive-artifacts binary resolution order: explicit env override (`ADAPTIVE_ARTIFACTS_BIN` / `ADAPTIVE_ARTIFACTS_ROOT`), then plugin-root / sibling plugin discovery, then PATH. `~/adaptive-artifacts` is not a quiet primary fallback.

## Invariants

- close-batch does not write the store; it only emits apply NDJSON.
- tdd/check results come from runner check-runs only.


## Assumptions

- Claude sets `CLAUDE_PLUGIN_ROOT`; Cursor sets `CURSOR_PLUGIN_ROOT` (or skills run from a tree where skill-relative plugin root works).
- Co-installed adaptive-artifacts is findable beside the se-workflow plugin root or on PATH after marketplace install.



### Decisions
- aa-resolve-order: env-plugin-root-path
