---
{
  "id": "rec-3a02d438-05d6-4fdb-a29a-d3c35a35c8fe",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-7e7db37d-173a-4938-93b0-91b2c18a98fc",
    "diff_sha256": "161f3b75895e00c660ddfc775462dbda20fa9010545d2144b0089fa20ce6b137",
    "duration_s": 0.661238,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_task_worktrees.py::test_r7_wave_end_merges_passing_task_branches_into_the_phase_branch"
    ],
    "informed_by": [
      "rec-7e7db37d-173a-4938-93b0-91b2c18a98fc"
    ],
    "method": "tdd",
    "output_sha256": "6ad704a34338ae094d84872c27d406a08d350ec9d629c3d0914828330bb9d99a",
    "requirement": "R7",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "skill-task-worktree-r7"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-21T05:00:10+00:00",
  "relationships": {},
  "revision": "sha256:062a119d13fef321af0ebce10acba03923baab7cc7366a5b9efbe3bbd025b0fa",
  "subject": "skill-task-worktree-r7",
  "time": {
    "observed": "2026-10-21T05:00:10+00:00",
    "recorded": "2026-10-21T05:00:10+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_____ test_r7_wave_end_merges_passing_task_branches_into_the_phase_branch ______
tests/test_task_worktrees.py:66: in test_r7_wave_end_merges_passing_task_branches_into_the_phase_branch
    assert (
E   AssertionError: assert 'At wave end, the parent merges each passing task branch of a task other than the work-item that depends_on every other phase work-item into `phase/<phase-slug>`.' in '--- name: execute-phase description: >- Dispatches orchestra work-items whose derived.ready is true, in dependency or...d`) and `manual`/`review` stay parent writes - Let a subagent sign an amendment or write `test_ids` / `oracle_hashes` '
=========================== short test summary info ============================
FAILED tests/test_task_worktrees.py::test_r7_wave_end_merges_passing_task_branches_into_the_phase_branch
1 failed in 0.05s
