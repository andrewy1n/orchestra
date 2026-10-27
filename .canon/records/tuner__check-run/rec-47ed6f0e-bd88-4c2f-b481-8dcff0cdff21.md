---
{
  "id": "rec-47ed6f0e-bd88-4c2f-b481-8dcff0cdff21",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-c1742922-b91e-449a-94bc-9fce443f6d88",
    "diff_sha256": "3e01708d3fdc41b03c546db46d9837a545d93941d468ea98c7bad98833cd7088",
    "duration_s": 0.581629,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_task_worktrees.py::test_r9_wave_end_integration_does_not_rebase_the_task_branch"
    ],
    "informed_by": [
      "rec-c1742922-b91e-449a-94bc-9fce443f6d88"
    ],
    "method": "tdd",
    "output_sha256": "6886309d3ce500115a1a6af15cd5ed36130c6c333d389dc2d50c49154a914a83",
    "requirement": "R9",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "skill-task-worktree-r9"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-21T05:32:45+00:00",
  "relationships": {},
  "revision": "sha256:3f0aa7a95798509e4c28cad2c67546bcc03307e26b8d9d2462254f7ee06d2c6b",
  "subject": "skill-task-worktree-r9",
  "time": {
    "observed": "2026-10-21T05:32:45+00:00",
    "recorded": "2026-10-21T05:32:45+00:00"
  }
}
---

F                                                                                                                                                                                                                                        [100%]
=================================================================================================================== FAILURES ===================================================================================================================
_________________________________________________________________________________________ test_r9_wave_end_integration_does_not_rebase_the_task_branch _________________________________________________________________________________________
tests/test_task_worktrees.py:80: in test_r9_wave_end_integration_does_not_rebase_the_task_branch
    assert "The wave-end integration does not rebase the task branch." in text
E   AssertionError: assert 'The wave-end integration does not rebase the task branch.' in '--- name: execute-phase description: >- Dispatches orchestra work-items whose derived.ready is true, in dependency or...d`) and `manual`/`review` stay parent writes - Let a subagent sign an amendment or write `test_ids` / `oracle_hashes` '
=========================================================================================================== short test summary info ============================================================================================================
FAILED tests/test_task_worktrees.py::test_r9_wave_end_integration_does_not_rebase_the_task_branch - AssertionError: assert 'The wave-end integration does not rebase the task branch.' in '--- name: execute-phase description: >- Dispatches...
1 failed in 0.05s
