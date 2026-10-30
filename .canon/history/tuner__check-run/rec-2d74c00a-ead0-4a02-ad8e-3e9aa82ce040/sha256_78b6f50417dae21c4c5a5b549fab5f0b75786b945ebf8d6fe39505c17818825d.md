---
{
  "id": "rec-2d74c00a-ead0-4a02-ad8e-3e9aa82ce040",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-0a62ac2f-60db-4a81-abb0-f0775120a43e",
    "duration_s": 0.533501,
    "effort": "session-handoff",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_hooks.py::test_r4_constraints_block_lists_constraints_from_every_live_effort"
    ],
    "informed_by": [
      "rec-0a62ac2f-60db-4a81-abb0-f0775120a43e"
    ],
    "method": "tdd",
    "output_sha256": "a2610d31c5fd767c04257577aa4299fe213bdebd96177996430778f5ed6cac4c",
    "requirement": "R4",
    "result": "fail",
    "revision": "e6b7d1957f66abc5fd41ebddb09e79ec74dc817a",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T08:28:08+00:00",
  "relationships": {},
  "revision": "sha256:78b6f50417dae21c4c5a5b549fab5f0b75786b945ebf8d6fe39505c17818825d",
  "subject": "compact-hook-view"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
______ test_r4_constraints_block_lists_constraints_from_every_live_effort ______

repo = Project(project_root=PosixPath('/tmp/pytest-of-andrewyin/pytest-560/test_r4_constraints_block_list0/repo'), store_path...ndrewyin/pytest-560/test_r4_constraints_block_list0/repo/.canon'), binding=Binding(location='local', source='default'))
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7777c6cd23f0>
capsys = <_pytest.capture.CaptureFixture object at 0x7777c6d34590>

    def test_r4_constraints_block_lists_constraints_from_every_live_effort(
        repo, monkeypatch, capsys
    ):
        add_effort(repo, "bravo")
        add_effort(repo, "charlie")
        add_constraint(repo, "alpha-rule", "Alpha stays small", "alpha")
        add_constraint(repo, "bravo-rule", "Bravo stays fast", "bravo")
        add_constraint(repo, "charlie-rule", "Charlie stays typed", "charlie")
        block = constraints_block(claude_context(repo, monkeypatch, capsys))
>       assert "Alpha stays small" in block
E       AssertionError: assert 'Alpha stays small' in 'Active constraints:\n- **charlie-rule**: Charlie stays typed\n\nOther views: `orchestra view plan|status|verification`.\n'

tests/test_hooks.py:361: AssertionError
=========================== short test summary info ============================
FAILED tests/test_hooks.py::test_r4_constraints_block_lists_constraints_from_every_live_effort
1 failed in 0.27s
warning: `VIRTUAL_ENV=/home/andrewyin/orchestra/.venv` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
