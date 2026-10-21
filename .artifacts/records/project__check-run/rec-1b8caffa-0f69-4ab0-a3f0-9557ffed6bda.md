---
{
  "base_kind": "event",
  "id": "rec-1b8caffa-0f69-4ab0-a3f0-9557ffed6bda",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-05063455-94b9-4240-a1c0-eda12599cf71",
    "diff_sha256": "3e01708d3fdc41b03c546db46d9837a545d93941d468ea98c7bad98833cd7088",
    "duration_s": 0.603267,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": "[\"tests/test_task_worktrees.py::test_r1_landing_creates_a_task_branch_except_the_verification_task\"]",
    "method": "tdd",
    "output_sha256": "3083d515c1d5d4f69b18bc9b96154b36e81c3ab7483742ff7853341df530a7ff",
    "requirement": "R1",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "skill-task-worktree"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-21T05:32:21+00:00",
  "relationships": {
    "informed_by": [
      "rec-05063455-94b9-4240-a1c0-eda12599cf71"
    ]
  },
  "revision": "sha256:5fe17b944941b6d9a7c68c87fe43ac29dad54a53b2007da920a4e84d164d41c5",
  "subject": "skill-task-worktree",
  "time": {
    "observed": "2026-10-21T05:32:21+00:00",
    "recorded": "2026-10-21T05:32:21+00:00"
  }
}
---

F                                                                                                                                                                                                                                        [100%]
=================================================================================================================== FAILURES ===================================================================================================================
______________________________________________________________________________________ test_r1_landing_creates_a_task_branch_except_the_verification_task ______________________________________________________________________________________
tests/test_task_worktrees.py:23: in test_r1_landing_creates_a_task_branch_except_the_verification_task
    assert (
E   AssertionError: assert 'When Landing is present, at the start of a wave, execute-phase creates branch `task/<phase-slug>/<task-slug>` from th...`phase/<phase-slug>` tip for every task in that wave except the work-item that depends_on every other phase work-item.' in '--- name: execute-phase description: >- Dispatches orchestra work-items whose derived.ready is true, in dependency or...d`) and `manual`/`review` stay parent writes - Let a subagent sign an amendment or write `test_ids` / `oracle_hashes` '
=========================================================================================================== short test summary info ============================================================================================================
FAILED tests/test_task_worktrees.py::test_r1_landing_creates_a_task_branch_except_the_verification_task - AssertionError: assert 'When Landing is present, at the start of a wave, execute-phase creates branch `task/<phase-slug>/<task-slug...
1 failed in 0.05s
