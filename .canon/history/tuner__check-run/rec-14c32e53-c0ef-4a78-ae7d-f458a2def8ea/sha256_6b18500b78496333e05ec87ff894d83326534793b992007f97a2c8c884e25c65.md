---
{
  "id": "rec-14c32e53-c0ef-4a78-ae7d-f458a2def8ea",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-05063455-94b9-4240-a1c0-eda12599cf71",
    "diff_sha256": "161f3b75895e00c660ddfc775462dbda20fa9010545d2144b0089fa20ce6b137",
    "duration_s": 0.565692,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_task_worktrees.py::test_r1_landing_creates_a_task_branch_except_the_verification_task"
    ],
    "informed_by": [
      "rec-05063455-94b9-4240-a1c0-eda12599cf71"
    ],
    "method": "tdd",
    "output_sha256": "0c3bc26dca047e08a8f72a998a81f3d44a8dcdbbc64cf544aac0aabdfc9811b8",
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
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-21T05:00:04+00:00",
  "relationships": {},
  "revision": "sha256:6b18500b78496333e05ec87ff894d83326534793b992007f97a2c8c884e25c65",
  "subject": "skill-task-worktree",
  "time": {
    "observed": "2026-10-21T05:00:04+00:00",
    "recorded": "2026-10-21T05:00:04+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
______ test_r1_landing_creates_a_task_branch_except_the_verification_task ______
tests/test_task_worktrees.py:23: in test_r1_landing_creates_a_task_branch_except_the_verification_task
    assert (
E   AssertionError: assert 'When Landing is present, at the start of a wave, execute-phase creates branch `task/<phase-slug>/<task-slug>` from th...`phase/<phase-slug>` tip for every task in that wave except the work-item that depends_on every other phase work-item.' in '--- name: execute-phase description: >- Dispatches orchestra work-items whose derived.ready is true, in dependency or...d`) and `manual`/`review` stay parent writes - Let a subagent sign an amendment or write `test_ids` / `oracle_hashes` '
=========================== short test summary info ============================
FAILED tests/test_task_worktrees.py::test_r1_landing_creates_a_task_branch_except_the_verification_task
1 failed in 0.05s
