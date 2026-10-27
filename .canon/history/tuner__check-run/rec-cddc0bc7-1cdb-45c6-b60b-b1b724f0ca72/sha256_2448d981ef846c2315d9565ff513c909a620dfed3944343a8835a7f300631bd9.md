---
{
  "id": "rec-cddc0bc7-1cdb-45c6-b60b-b1b724f0ca72",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-9978c80a-6e9e-4a29-963c-5cdd28a10718",
    "diff_sha256": "161f3b75895e00c660ddfc775462dbda20fa9010545d2144b0089fa20ce6b137",
    "duration_s": 0.613989,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_task_worktrees.py::test_r3_per_task_commit_runs_in_that_task_worktree"
    ],
    "informed_by": [
      "rec-9978c80a-6e9e-4a29-963c-5cdd28a10718"
    ],
    "method": "tdd",
    "output_sha256": "a4920f68db7f0969cb16d625bf92a2f95664fe0184a111f20426594de2334bb4",
    "requirement": "R3",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "skill-task-worktree-r3"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-21T05:00:06+00:00",
  "relationships": {},
  "revision": "sha256:2448d981ef846c2315d9565ff513c909a620dfed3944343a8835a7f300631bd9",
  "subject": "skill-task-worktree-r3",
  "time": {
    "observed": "2026-10-21T05:00:06+00:00",
    "recorded": "2026-10-21T05:00:06+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
______________ test_r3_per_task_commit_runs_in_that_task_worktree ______________
tests/test_task_worktrees.py:43: in test_r3_per_task_commit_runs_in_that_task_worktree
    assert f"The per-task commit for {_OTHER} runs in that task worktree." in text
E   AssertionError: assert 'The per-task commit for a task other than the work-item that depends_on every other phase work-item runs in that task worktree.' in '--- name: execute-phase description: >- Dispatches orchestra work-items whose derived.ready is true, in dependency or...d`) and `manual`/`review` stay parent writes - Let a subagent sign an amendment or write `test_ids` / `oracle_hashes` '
=========================== short test summary info ============================
FAILED tests/test_task_worktrees.py::test_r3_per_task_commit_runs_in_that_task_worktree
1 failed in 0.05s
