---
{
  "base_kind": "event",
  "id": "rec-91b4b740-edbe-4b26-aefb-528dfca19488",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-fecf70a3-9dff-4199-8d1a-cb9a3e7e3fe2",
    "diff_sha256": "3e01708d3fdc41b03c546db46d9837a545d93941d468ea98c7bad98833cd7088",
    "duration_s": 0.560397,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": "[\"tests/test_task_worktrees.py::test_r24_orientation_names_the_task_worktree_as_the_write_root\"]",
    "method": "tdd",
    "output_sha256": "659fa00986118b633ca5bb846db44101cb771ce07272f8789136e48d65d53786",
    "requirement": "R24",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "skill-task-worktree-r24"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-21T05:32:35+00:00",
  "relationships": {
    "informed_by": [
      "rec-fecf70a3-9dff-4199-8d1a-cb9a3e7e3fe2"
    ]
  },
  "revision": "sha256:d15d45c57b65badf03ca6a9ae8f4bff80b57c1b860706697d885f96c4568d94e",
  "subject": "skill-task-worktree-r24",
  "time": {
    "observed": "2026-10-21T05:32:35+00:00",
    "recorded": "2026-10-21T05:32:35+00:00"
  }
}
---

F                                                                                                                                                                                                                                        [100%]
=================================================================================================================== FAILURES ===================================================================================================================
________________________________________________________________________________________ test_r24_orientation_names_the_task_worktree_as_the_write_root ________________________________________________________________________________________
tests/test_task_worktrees.py:198: in test_r24_orientation_names_the_task_worktree_as_the_write_root
    assert (
E   assert "The assignment orientation names that task worktree as the executor's write root." in '--- name: execute-phase description: >- Dispatches orchestra work-items whose derived.ready is true, in dependency or...d`) and `manual`/`review` stay parent writes - Let a subagent sign an amendment or write `test_ids` / `oracle_hashes` '
=========================================================================================================== short test summary info ============================================================================================================
FAILED tests/test_task_worktrees.py::test_r24_orientation_names_the_task_worktree_as_the_write_root - assert "The assignment orientation names that task worktree as the executor's write root." in '--- name: execute-phase description: >- ...
1 failed in 0.05s
