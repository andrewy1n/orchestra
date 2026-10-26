---
{
  "id": "rec-2baf627f-eba5-4ede-b2f7-dd5e34b443b7",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-d3795838-1047-40f0-ad9b-a8523c5ca6c2",
    "diff_sha256": "161f3b75895e00c660ddfc775462dbda20fa9010545d2144b0089fa20ce6b137",
    "duration_s": 0.566035,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_task_worktrees.py::test_r11_conflict_leaves_that_conflict_unresolved"
    ],
    "informed_by": [
      "rec-d3795838-1047-40f0-ad9b-a8523c5ca6c2"
    ],
    "method": "tdd",
    "output_sha256": "12ad8c958dd4ac92f867b483eca86e62bca4d798ac0a544f4b37f5673b0d5d65",
    "requirement": "R11",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "skill-task-worktree-r11"
    ]
  },
  "record_type": "aff:check-run",
  "recorded_at": "2026-10-21T05:00:14+00:00",
  "relationships": {},
  "revision": "sha256:564dcafe397338a0392c59d3a170847a70b5420947114877c78180ec339d6d9c",
  "subject": "skill-task-worktree-r11",
  "time": {
    "observed": "2026-10-21T05:00:14+00:00",
    "recorded": "2026-10-21T05:00:14+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
______________ test_r11_conflict_leaves_that_conflict_unresolved _______________
tests/test_task_worktrees.py:90: in test_r11_conflict_leaves_that_conflict_unresolved
    assert (
E   AssertionError: assert 'When a merge between a task branch and the phase branch conflicts, the parent leaves that conflict unresolved.' in '--- name: execute-phase description: >- Dispatches orchestra work-items whose derived.ready is true, in dependency or...d`) and `manual`/`review` stay parent writes - Let a subagent sign an amendment or write `test_ids` / `oracle_hashes` '
=========================== short test summary info ============================
FAILED tests/test_task_worktrees.py::test_r11_conflict_leaves_that_conflict_unresolved
1 failed in 0.05s
