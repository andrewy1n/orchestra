---
{
  "base_kind": "event",
  "id": "rec-2c9aa2bf-ccce-422e-afcc-a094c9c81966",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-1848327f-f58b-4e72-aeb3-ae082358e7c4",
    "diff_sha256": "0f8d6d7525693b98d86ae479204bdc2322db4574966834057733cac4da9aa701",
    "duration_s": 0.627808,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": "[\"tests/test_task_commit.py::test_r27_per_task_commit_path_is_the_task_worktree\"]",
    "method": "tdd",
    "output_sha256": "89bdaa3586740345f32654dabc7a71fd1c7b53c8cd2bfac40668bdaf9e2b91af",
    "requirement": "R27",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "skill-task-worktree-r27"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-21T05:21:31+00:00",
  "relationships": {
    "informed_by": [
      "rec-1848327f-f58b-4e72-aeb3-ae082358e7c4"
    ]
  },
  "revision": "sha256:98a602b61f4c324cd53f57ed74ba52761778c5ec391a6c5f67d8088557c4ceb6",
  "subject": "skill-task-worktree-r27",
  "time": {
    "observed": "2026-10-21T05:21:31+00:00",
    "recorded": "2026-10-21T05:21:31+00:00"
  }
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
______________ test_r27_per_task_commit_path_is_the_task_worktree ______________
tests/test_task_commit.py:114: in test_r27_per_task_commit_path_is_the_task_worktree
    assert "git -C <repo>/.worktrees/<phase-slug>--<task-slug> commit" in text
E   AssertionError: assert 'git -C <repo>/.worktrees/<phase-slug>--<task-slug> commit' in '--- name: execute-phase description: >- Dispatches orchestra work-items whose derived.ready is true, in dependency or...d`) and `manual`/`review` stay parent writes - Let a subagent sign an amendment or write `test_ids` / `oracle_hashes` '
=========================== short test summary info ============================
FAILED tests/test_task_commit.py::test_r27_per_task_commit_path_is_the_task_worktree
1 failed in 0.05s
