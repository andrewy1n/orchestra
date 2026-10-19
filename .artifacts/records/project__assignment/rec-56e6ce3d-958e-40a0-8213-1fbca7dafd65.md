---
{
  "base_kind": "instruction",
  "id": "rec-56e6ce3d-958e-40a0-8213-1fbca7dafd65",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "workflow-loop",
    "executor": "tier2-engine-worker",
    "work_item": "tier2-engine"
  },
  "provenance": {
    "sources": [
      "tier2-engine"
    ]
  },
  "record_type": "project:assignment",
  "recorded_at": "2026-10-11T09:36:22+00:00",
  "relationships": {},
  "revision": "sha256:6d86ab71ec7da3ac8d2caecd9063a74bb03fd82e70d16af7ffda5cbb60e7d208",
  "subject": "tier2-engine",
  "time": {
    "observed": "2026-10-11T09:36:22+00:00",
    "recorded": "2026-10-11T09:36:22+00:00"
  }
}
---

## Orientation

Worktree (code only): `/home/andrewyin/se-workflow--tiered-verification` on branch `phase/tiered-verification`.
Primary checkout stays on `main` for store — you must NOT write `.artifacts/` or call `adaptive-artifacts`.
Territory: you own `se_workflow/`, `skills/`, `README.md`, `tests/test_tiered_verification.py`, `tests/test_verify_budget.py`. Do not edit `dashboard/`. Concurrent `tier2-dashboard-worker` owns dashboard only.
After code lands, commit on the phase branch excluding `.artifacts`: `git -C /home/andrewyin/se-workflow--tiered-verification add -A -- . ':!.artifacts' && git commit -m tier2-engine`. Put that SHA in evidence `revision`.

### Requirements (quoted)
R1: Per-task verification stays the existing scoped `verify_command` (and phase verification acceptances); this phase does not require affected-test selection (testmon or path map).
R2: Once per phase, after closing verification and the phase-end reviewer have passed, and before merge to `main`, the parent starts the full non-tmux suite (README fast form) plus the serial tmux leg in a background tmux window in the phase worktree, without blocking the agent session on the run.
R3: The runner records one `project:check-run` for the tier-2 run with integration/regression evidence kind as designed, `revision` = phase head SHA, exit code, duration, output digest, and failing node IDs when failed.
R4: The phase gate requires (a) every active phase acceptance has a passing runner check-run at the phase head SHA and (b) a passing tier-2 check-run at that same SHA before close/merge.
R5: A tier-2 failure produces fix work-item(s) under the retry-loop budget (clustered by failing test file/module); there is no inline fix-and-rerun inside the verification step. After fixes, tier-2 reruns at the new head.
R7: Skills and verify-budget tests are updated so per-task verification stays scoped while the phase-level full run is required.

### Design Invariants
- Per-task verification stays scoped.
- Tier-2 is required at head before merge.
- Failures become fix tasks under retry budget.

### Design Assumptions
- tmux and phase worktrees remain part of the operator setup.
- Head SHA is a real commit (task-commit-evidence); dirty-only tier-2 is refused or recorded consistently with dirty-pass policy.

### Decisions
- tiered-verification-scope: Tier-2 first: background full suite at head + gate + fix tasks; defer affected-test selection and flaky auto-retry polish
- tier2-execution: Background tmux full suite in the phase worktree
