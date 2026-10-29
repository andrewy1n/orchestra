---
{
  "id": "rec-edb9fdb8-7749-4e7e-baf6-f75d0a3bf1c3",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-83d957d0-ff20-4981-8dd7-c6294ed9e7a0",
    "duration_s": 1.332771,
    "effort": "session-handoff",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_hooks.py::test_r8_over_budget_start_context_omits_whole_effort_sections_only"
    ],
    "informed_by": [
      "rec-83d957d0-ff20-4981-8dd7-c6294ed9e7a0"
    ],
    "method": "tdd",
    "output_sha256": "0e87423c8178ca6194bc0e56d6bee88a3f08b7946255cc72edaa2a9834bf8eb3",
    "requirement": "R8",
    "result": "fail",
    "revision": "e6b7d1957f66abc5fd41ebddb09e79ec74dc817a",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T08:28:20+00:00",
  "relationships": {},
  "revision": "sha256:4c28d8afebc86409352fe5cf2600f28536ab9ceedf0e686915c4b6b53827873a",
  "subject": "hook-budget-whole"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
______ test_r8_over_budget_start_context_omits_whole_effort_sections_only ______

repo = Project(project_root=PosixPath('/tmp/pytest-of-andrewyin/pytest-566/test_r8_over_budget_start_cont0/repo'), store_path...ndrewyin/pytest-566/test_r8_over_budget_start_cont0/repo/.canon'), binding=Binding(location='local', source='default'))
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x71522ad5a3f0>
capsys = <_pytest.capture.CaptureFixture object at 0x71522adbc590>

    def test_r8_over_budget_start_context_omits_whole_effort_sections_only(
        repo, monkeypatch, capsys
    ):
        owned = crowd_store(repo)
        ctx = claude_context(repo, monkeypatch, capsys)
        shown = effort_sections(ctx)
        included = [slug for slug in CROWD if slug in shown]
        omitted = [slug for slug in CROWD if slug not in shown]
        assert included
        assert omitted
        for slug in included:
            assert f"Goal of {slug}" in ctx
>           assert [s for s in owned[slug] if s not in ctx] == []
E           AssertionError: assert ['golf-task-0...manual-check'] == []
E
E             Left contains 6 more items, first extra item: 'golf-task-0'
E             Use -v to get more diff

tests/test_hooks.py:419: AssertionError
=========================== short test summary info ============================
FAILED tests/test_hooks.py::test_r8_over_budget_start_context_omits_whole_effort_sections_only
1 failed in 1.09s
warning: `VIRTUAL_ENV=/home/andrewyin/orchestra/.venv` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
