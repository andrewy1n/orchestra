---
{
  "id": "rec-ccff30bd-f86b-4c6f-b95b-a642633189ed",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-e2d33f8f-465d-4c3a-9cae-fa60fb219f3c",
    "diff_sha256": "0f8d6d7525693b98d86ae479204bdc2322db4574966834057733cac4da9aa701",
    "duration_s": 0.567802,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_task_worktrees.py::test_r13_conflict_does_not_start_the_next_wave"
    ],
    "informed_by": [
      "rec-e2d33f8f-465d-4c3a-9cae-fa60fb219f3c"
    ],
    "method": "tdd",
    "output_sha256": "3c5ddd2fa9f0b97828b6ec81d342af70e41f0487bf8ece680a01e17b27c7644d",
    "requirement": "R13",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "skill-task-worktree-r13"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-21T05:21:18+00:00",
  "relationships": {},
  "revision": "sha256:a34dc7479b543eb18dd6ff57446bc2f14314c7d2fdde4d47d23c6a47b94feb28",
  "subject": "skill-task-worktree-r13",
  "time": {
    "observed": "2026-10-21T05:21:18+00:00",
    "recorded": "2026-10-21T05:21:18+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
________________ test_r13_conflict_does_not_start_the_next_wave ________________
tests/test_task_worktrees.py:108: in test_r13_conflict_does_not_start_the_next_wave
    assert (
E   AssertionError: assert 'When a merge between a task branch and the phase branch conflicts, the parent does not start the next wave.' in '--- name: execute-phase description: >- Dispatches orchestra work-items whose derived.ready is true, in dependency or...d`) and `manual`/`review` stay parent writes - Let a subagent sign an amendment or write `test_ids` / `oracle_hashes` '
=========================== short test summary info ============================
FAILED tests/test_task_worktrees.py::test_r13_conflict_does_not_start_the_next_wave
1 failed in 0.05s
