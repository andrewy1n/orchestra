---
{
  "id": "rec-0a0c49cb-a31c-4ff7-bcf4-bef2820794d7",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-4591df96-ffef-4618-8e6e-07d98f9b4347",
    "diff_sha256": "0f8d6d7525693b98d86ae479204bdc2322db4574966834057733cac4da9aa701",
    "duration_s": 0.565822,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_task_worktrees.py::test_r16_redispatch_merges_the_phase_tip_into_the_task_branch"
    ],
    "informed_by": [
      "rec-4591df96-ffef-4618-8e6e-07d98f9b4347"
    ],
    "method": "tdd",
    "output_sha256": "60c16c88b0b66dfac0056d0d83a5303457e053ebe2fbe7171065f4c1df7bcb63",
    "requirement": "R16",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "skill-task-worktree-r16"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-21T05:21:21+00:00",
  "relationships": {},
  "revision": "sha256:05f58222818d7e29cc287c007911be6355d142617a0e6f2fd28e132e9de70741",
  "subject": "skill-task-worktree-r16",
  "time": {
    "observed": "2026-10-21T05:21:21+00:00",
    "recorded": "2026-10-21T05:21:21+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
________ test_r16_redispatch_merges_the_phase_tip_into_the_task_branch _________
tests/test_task_worktrees.py:134: in test_r16_redispatch_merges_the_phase_tip_into_the_task_branch
    assert (
E   AssertionError: assert 'Before a re-dispatch continues, the parent merges `phase/<phase-slug>` into the task branch when the task branch does not already contain the phase tip.' in '--- name: execute-phase description: >- Dispatches orchestra work-items whose derived.ready is true, in dependency or...d`) and `manual`/`review` stay parent writes - Let a subagent sign an amendment or write `test_ids` / `oracle_hashes` '
=========================== short test summary info ============================
FAILED tests/test_task_worktrees.py::test_r16_redispatch_merges_the_phase_tip_into_the_task_branch
1 failed in 0.05s
