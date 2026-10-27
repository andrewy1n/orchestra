---
{
  "id": "rec-dc423ffd-8090-4b8f-9efb-ff863fcc3952",
  "lifecycle_state": "recorded",
  "payload": {
    "assignment": "move-effort-records",
    "result": "fail",
    "revision": "dirty",
    "verdict": "fail",
    "work_item": "move-effort-records"
  },
  "provenance": {
    "sources": [
      "move-effort-records"
    ]
  },
  "record_type": "conductor:execution-report",
  "recorded_at": "2026-10-17T08:16:41+00:00",
  "relationships": {},
  "revision": "sha256:89c77c4ba601b113c6fff7b20103af1f553f0e4c1ae8c46403ca00be6a6cdaa9",
  "subject": "move-effort-records",
  "time": {
    "observed": "2026-10-17T08:16:41+00:00",
    "recorded": "2026-10-17T08:16:41+00:00"
  }
}
---

subject: move-effort-records
kind: deliver
result: fail
revision: dirty
evidence: |
  orchestra.project_field.rewrite_project_field rewrote .artifacts/project-design.json from affidavit to orchestra, the store was copied to ~/orchestra/.artifacts, and record files were moved with their log and history directories.
  Active goals here: ["evidence-layer"]
  Active goals in ~/orchestra/.artifacts: ["dashboard", "packaging", "session-analysis", "test-suite-speed", "workflow-loop"]
  adaptive-artifacts validate in this checkout exits 4. The errors are immutability violations: git diff HEAD shows the moved record, log, and history paths as deleted.
  adaptive-artifacts validate in ~/orchestra exits 4 with seven errors that also fail on the phase worktree's committed store, before this move: a check-run whose result is tdd, two active project:release records for tiered-verification, that check-run having two correcting successors, two execution-reports whose assignment subject matches no assignment, and two history snapshots whose revision does not match their bytes.
observations: The goal lists match the acceptance. Validate does not. One evidence-kind phase record is in both stores because an orchestra record references that phase subject. Record bytes that stayed were not edited. meta.json contract_digest was re-pinned to the resolved contract after resolve.
root_cause: Uncommitted deletion of git-tracked store paths fails the immutability check, and seven pre-existing records fail validate in whichever store holds them.
verdict: fail
metrics:
claim:
needs_human: true
attempted_action:
retry_when:
blocker: validate fails in both stores
