---
{
  "base_kind": "event",
  "id": "rec-0ce05df9-4fec-49fa-80ec-5a82c1d5781d",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-6f21fdb6-ed88-4965-a020-b9e9b386f343",
    "diff_sha256": "0f8d6d7525693b98d86ae479204bdc2322db4574966834057733cac4da9aa701",
    "duration_s": 0.587981,
    "effort": "workflow-loop",
    "exit_code": 1,
    "failing_node_ids": "[\"tests/test_task_worktrees.py::test_r20_absent_landing_does_not_create_a_task_branch\", \"tests/test_execute_landing.py::test_landing_worktree_confines_code_and_keeps_the_store_on_the_primary_checkout\", \"tests/test_execute_landing.py::test_gate_commits_the_phase_branch_merges_to_main_and_commits_the_store\", \"tests/test_execute_landing.py::test_push_only_when_it_is_a_human_stop\", \"tests/test_execute_landing.py::test_missing_landing_section_stays_in_the_current_checkout\"]",
    "method": "tdd",
    "output_sha256": "b7ece694b7c16fb597b236e8dad98f64fbae752c8d8a1ea22b4e0747c448868a",
    "requirement": "R20",
    "result": "fail",
    "revision": "dirty",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "skill-task-worktree-r20"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-21T05:21:26+00:00",
  "relationships": {
    "informed_by": [
      "rec-6f21fdb6-ed88-4965-a020-b9e9b386f343"
    ]
  },
  "revision": "sha256:3d10e5638e65e567a0ca7b93b952f21592b31f5b16f831aad2172e0e269f6d65",
  "subject": "skill-task-worktree-r20",
  "time": {
    "observed": "2026-10-21T05:21:26+00:00",
    "recorded": "2026-10-21T05:21:26+00:00"
  }
}
---

FFFFF                                                                    [100%]
=================================== FAILURES ===================================
____________ test_r20_absent_landing_does_not_create_a_task_branch _____________
tests/test_task_worktrees.py:162: in test_r20_absent_landing_does_not_create_a_task_branch
    assert (
E   AssertionError: assert 'When Landing is absent, execute-phase does not create a `task/<phase-slug>/<task-slug>` branch.' in '--- name: execute-phase description: >- Dispatches orchestra work-items whose derived.ready is true, in dependency or...d`) and `manual`/`review` stay parent writes - Let a subagent sign an amendment or write `test_ids` / `oracle_hashes` '
_ test_landing_worktree_confines_code_and_keeps_the_store_on_the_primary_checkout _
tests/test_execute_landing.py:20: in test_landing_worktree_confines_code_and_keeps_the_store_on_the_primary_checkout
    assert "code writes only under the worktree" in text
E   AssertionError: assert 'code writes only under the worktree' in '--- name: execute-phase description: >- Dispatches orchestra work-items whose derived.ready is true, in dependency or...d`) and `manual`/`review` stay parent writes - Let a subagent sign an amendment or write `test_ids` / `oracle_hashes` '
___ test_gate_commits_the_phase_branch_merges_to_main_and_commits_the_store ____
tests/test_execute_landing.py:26: in test_gate_commits_the_phase_branch_merges_to_main_and_commits_the_store
    assert "commit the phase branch" in text
E   AssertionError: assert 'commit the phase branch' in '--- name: execute-phase description: >- Dispatches orchestra work-items whose derived.ready is true, in dependency or...d`) and `manual`/`review` stay parent writes - Let a subagent sign an amendment or write `test_ids` / `oracle_hashes` '
____________________ test_push_only_when_it_is_a_human_stop ____________________
tests/test_execute_landing.py:33: in test_push_only_when_it_is_a_human_stop
    assert "push only when it is a human stop" in text
E   AssertionError: assert 'push only when it is a human stop' in '--- name: execute-phase description: >- Dispatches orchestra work-items whose derived.ready is true, in dependency or...d`) and `manual`/`review` stay parent writes - Let a subagent sign an amendment or write `test_ids` / `oracle_hashes` '
__________ test_missing_landing_section_stays_in_the_current_checkout __________
tests/test_execute_landing.py:38: in test_missing_landing_section_stays_in_the_current_checkout
    assert "a missing Landing section stays in the current checkout" in text
E   AssertionError: assert 'a missing Landing section stays in the current checkout' in '--- name: execute-phase description: >- Dispatches orchestra work-items whose derived.ready is true, in dependency or...d`) and `manual`/`review` stay parent writes - Let a subagent sign an amendment or write `test_ids` / `oracle_hashes` '
=========================== short test summary info ============================
FAILED tests/test_task_worktrees.py::test_r20_absent_landing_does_not_create_a_task_branch
FAILED tests/test_execute_landing.py::test_landing_worktree_confines_code_and_keeps_the_store_on_the_primary_checkout
FAILED tests/test_execute_landing.py::test_gate_commits_the_phase_branch_merges_to_main_and_commits_the_store
FAILED tests/test_execute_landing.py::test_push_only_when_it_is_a_human_stop
FAILED tests/test_execute_landing.py::test_missing_landing_section_stays_in_the_current_checkout
5 failed in 0.06s
