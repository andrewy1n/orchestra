---
{
  "id": "rec-c2d66da3-7ff8-46da-b2e7-5b49cf62b1c6",
  "lifecycle_state": "asserted",
  "payload": {
    "basis": "Main split dashboard/model.py into backend modules, moved dashboard/web to dashboard/backend/server, and deleted the stdlib server. phase/shared-helpers merged main (commit b1ebc9eba). The shared route table and the stdlib/FastAPI parity no longer apply because one FastAPI server remains, so tests R12, R13, R14 and tests/test_route_parity.py were removed; R17, R18, R22, R23 and R6 now point at dashboard/backend/records.py, approval.py and landing.py; the record_payload change was ported onto records.py, task.py, phase.py, snapshot.py, journal.py and areas.py.",
    "claim": "phase/shared-helpers now contains main; R12 to R14 (route table) have no tests",
    "effort": "package-layout",
    "invalidated_when": "The owner of shared-helpers decides the route-table requirements stay and restores them against the FastAPI app, or supersedes R12 to R14",
    "needs": "human"
  },
  "record_type": "tuner:finding",
  "recorded_at": "2026-10-30T00:36:38+00:00",
  "relationships": {},
  "revision": "sha256:7f74401482b107524b0854a2bb5942d5d1fe3bdc8da13d42ca80386f6dbf8672",
  "subject": "shared-helpers-merged-main"
}
---

## Evidence

The merge ran in .worktrees/shared-helpers. Conflicts were the deleted dashboard files and orchestra/views.py. After the port, the full suite (1273 passed), tests/canon, tests/tuner, basedpyright and ruff pass on the branch. Oracle hashes for the acceptances on tests/test_shared_helpers.py were re-frozen.

## Consequence

Acceptances dashboard-routes (R12), dashboard-routes-stdlib (R13), dashboard-routes-fastapi (R14), fix-route-parity and verify-shared-helpers-routes name tests that no longer exist. The unfinished task branches (task/shared-helpers/*) are behind phase/shared-helpers; re-dispatch merges the phase tip into them.

## Follow-up

Decide whether to drop or rewrite R12 to R14 for the single server, then adjust the dashboard-routes work-item and its acceptances.
