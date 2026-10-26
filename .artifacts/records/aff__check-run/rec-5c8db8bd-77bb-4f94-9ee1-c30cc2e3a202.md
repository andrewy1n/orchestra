---
{
  "id": "rec-5c8db8bd-77bb-4f94-9ee1-c30cc2e3a202",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-29827ca8-3bb5-474e-bc9d-e9f27c9cb64b",
    "diff_sha256": "fecefc44d34aeab5e708cbfea2b8ba15dcee3636e74a2160a878fda6f0e5485d",
    "duration_s": 0.579417,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_task_worktrees.py::test_r6_passing_check_run_records_that_task_commit"
    ],
    "informed_by": [
      "rec-29827ca8-3bb5-474e-bc9d-e9f27c9cb64b"
    ],
    "method": "tdd",
    "output_sha256": "4f1d8aee6636e2bd8afb5ff8bbaebcc8e53fbe9c89d99cd53cf32b36c9d10c14",
    "requirement": "R6",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "skill-task-worktree-r6"
    ]
  },
  "record_type": "aff:check-run",
  "recorded_at": "2026-10-21T05:34:24+00:00",
  "relationships": {},
  "revision": "sha256:ebfd00dfe3cdb85f84ada31d984eae1113ee1077f5d3968cb47f98db6eee5901",
  "subject": "skill-task-worktree-r6",
  "time": {
    "observed": "2026-10-21T05:34:24+00:00",
    "recorded": "2026-10-21T05:34:24+00:00"
  }
}
---

F                                                                                                                                                                                                                                        [100%]
=================================================================================================================== FAILURES ===================================================================================================================
______________________________________________________________________________________________ test_r6_passing_check_run_records_that_task_commit ______________________________________________________________________________________________
tests/test_task_worktrees.py:59: in test_r6_passing_check_run_records_that_task_commit
    f"A passing check-run for {_OTHER} records that task's commit as its revision."
E   AssertionError
=========================================================================================================== short test summary info ============================================================================================================
FAILED tests/test_task_worktrees.py::test_r6_passing_check_run_records_that_task_commit - AssertionError
1 failed in 0.05s
