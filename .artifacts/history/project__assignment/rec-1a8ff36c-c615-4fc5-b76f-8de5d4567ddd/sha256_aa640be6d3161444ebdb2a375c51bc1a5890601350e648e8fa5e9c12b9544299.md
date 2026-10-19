---
{
  "base_kind": "instruction",
  "id": "rec-1a8ff36c-c615-4fc5-b76f-8de5d4567ddd",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "workflow-loop",
    "executor": "tier2-dashboard-worker",
    "work_item": "tier2-dashboard"
  },
  "provenance": {
    "sources": [
      "tier2-dashboard"
    ]
  },
  "record_type": "project:assignment",
  "recorded_at": "2026-10-11T09:36:22+00:00",
  "relationships": {},
  "revision": "sha256:aa640be6d3161444ebdb2a375c51bc1a5890601350e648e8fa5e9c12b9544299",
  "subject": "tier2-dashboard",
  "time": {
    "observed": "2026-10-11T09:36:22+00:00",
    "recorded": "2026-10-11T09:36:22+00:00"
  }
}
---

## Orientation

Worktree (code only): `/home/andrewyin/se-workflow--tiered-verification` on branch `phase/tiered-verification`.
Primary checkout stays on `main` for store — you must NOT write `.artifacts/` or call `adaptive-artifacts`.
Territory: you own `dashboard/` and dashboard pilots (`tests/test_dashboard_app.py`, `tests/test_dashboard_model.py` only as needed for tier-2 header). Do not edit `se_workflow/`, `skills/`, `README.md`, or `tests/test_tiered_verification.py` / `tests/test_verify_budget.py` (owned by concurrent `tier2-engine-worker`).
Agree subject/evidence convention with engine: tier-2 check-runs use subject `<phase>-tier2` and `evidence_kind: integration`. If engine has not landed yet, seed fixtures in tests accordingly.
After code lands, commit on the phase branch excluding `.artifacts`: `git -C /home/andrewyin/se-workflow--tiered-verification add -A -- . ':!.artifacts' && git commit -m tier2-dashboard`. Put that SHA in evidence `revision`.

### Requirements (quoted)
R6: The dashboard shows tier-2 status on the phase header (running / passed / failed at SHA).

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
