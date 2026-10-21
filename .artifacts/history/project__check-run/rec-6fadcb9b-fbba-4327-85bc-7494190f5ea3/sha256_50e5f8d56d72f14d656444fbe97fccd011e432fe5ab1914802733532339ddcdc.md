---
{
  "base_kind": "event",
  "id": "rec-6fadcb9b-fbba-4327-85bc-7494190f5ea3",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-ef7174ed-e462-4077-8933-95f77cac0ce2",
    "diff_sha256": "161f3b75895e00c660ddfc775462dbda20fa9010545d2144b0089fa20ce6b137",
    "duration_s": 0.610672,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": "[\"tests/test_task_worktrees.py::test_r4_per_task_commit_stages_with_git_add_excluding_artifacts\"]",
    "method": "tdd",
    "output_sha256": "1607cdd4e8033f01ac8024d78bcd4727d242e63e1df0512fc37c739a7fd76ba0",
    "requirement": "R4",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "skill-task-worktree-r4"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-21T05:00:07+00:00",
  "relationships": {
    "informed_by": [
      "rec-ef7174ed-e462-4077-8933-95f77cac0ce2"
    ]
  },
  "revision": "sha256:50e5f8d56d72f14d656444fbe97fccd011e432fe5ab1914802733532339ddcdc",
  "subject": "skill-task-worktree-r4",
  "time": {
    "observed": "2026-10-21T05:00:07+00:00",
    "recorded": "2026-10-21T05:00:07+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
_______ test_r4_per_task_commit_stages_with_git_add_excluding_artifacts ________
tests/test_task_worktrees.py:48: in test_r4_per_task_commit_stages_with_git_add_excluding_artifacts
    assert "That per-task commit stages with `git add -A` excluding `.artifacts`." in text
E   AssertionError: assert 'That per-task commit stages with `git add -A` excluding `.artifacts`.' in '--- name: execute-phase description: >- Dispatches orchestra work-items whose derived.ready is true, in dependency or...d`) and `manual`/`review` stay parent writes - Let a subagent sign an amendment or write `test_ids` / `oracle_hashes` '
=========================== short test summary info ============================
FAILED tests/test_task_worktrees.py::test_r4_per_task_commit_stages_with_git_add_excluding_artifacts
1 failed in 0.05s
