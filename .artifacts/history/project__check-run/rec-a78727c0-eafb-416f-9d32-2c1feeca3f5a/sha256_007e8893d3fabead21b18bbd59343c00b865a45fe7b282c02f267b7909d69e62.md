---
{
  "base_kind": "event",
  "id": "rec-a78727c0-eafb-416f-9d32-2c1feeca3f5a",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-4591df96-ffef-4618-8e6e-07d98f9b4347",
    "diff_sha256": "3e01708d3fdc41b03c546db46d9837a545d93941d468ea98c7bad98833cd7088",
    "duration_s": 0.588991,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": "[\"tests/test_task_worktrees.py::test_r16_redispatch_merges_the_phase_tip_into_the_task_branch\"]",
    "method": "tdd",
    "output_sha256": "efd0d3ae655914f4f3b7b2185e092c5975be094bcd75bd9cbedb5f42fca07c06",
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
  "record_type": "project:check-run",
  "recorded_at": "2026-10-21T05:32:28+00:00",
  "relationships": {
    "informed_by": [
      "rec-4591df96-ffef-4618-8e6e-07d98f9b4347"
    ]
  },
  "revision": "sha256:007e8893d3fabead21b18bbd59343c00b865a45fe7b282c02f267b7909d69e62",
  "subject": "skill-task-worktree-r16",
  "time": {
    "observed": "2026-10-21T05:32:28+00:00",
    "recorded": "2026-10-21T05:32:28+00:00"
  }
}
---

F                                                                                                                                                                                                                                        [100%]
=================================================================================================================== FAILURES ===================================================================================================================
________________________________________________________________________________________ test_r16_redispatch_merges_the_phase_tip_into_the_task_branch _________________________________________________________________________________________
tests/test_task_worktrees.py:134: in test_r16_redispatch_merges_the_phase_tip_into_the_task_branch
    assert (
E   AssertionError: assert 'Before a re-dispatch continues, the parent merges `phase/<phase-slug>` into the task branch when the task branch does not already contain the phase tip.' in '--- name: execute-phase description: >- Dispatches orchestra work-items whose derived.ready is true, in dependency or...d`) and `manual`/`review` stay parent writes - Let a subagent sign an amendment or write `test_ids` / `oracle_hashes` '
=========================================================================================================== short test summary info ============================================================================================================
FAILED tests/test_task_worktrees.py::test_r16_redispatch_merges_the_phase_tip_into_the_task_branch - AssertionError: assert 'Before a re-dispatch continues, the parent merges `phase/<phase-slug>` into the task branch when the task branch...
1 failed in 0.05s
