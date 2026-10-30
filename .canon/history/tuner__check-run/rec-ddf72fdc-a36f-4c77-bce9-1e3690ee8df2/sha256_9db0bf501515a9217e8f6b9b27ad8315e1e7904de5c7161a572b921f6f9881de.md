---
{
  "id": "rec-ddf72fdc-a36f-4c77-bce9-1e3690ee8df2",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-69a7e3f2-bcc3-4461-8ec4-7baea80e817f",
    "duration_s": 1.439949,
    "effort": "session-handoff",
    "exit_code": 1,
    "failing_node_ids": [
      "tests/test_hooks.py::test_r12_plain_start_context_matches_claude_budget_and_content"
    ],
    "informed_by": [
      "rec-69a7e3f2-bcc3-4461-8ec4-7baea80e817f"
    ],
    "method": "tdd",
    "output_sha256": "d290d6dc937f50284d76bf4e5cf9c81e55fadca9c58f79276587ebebc80bb9f3",
    "requirement": "R12",
    "result": "fail",
    "revision": "e6b7d1957f66abc5fd41ebddb09e79ec74dc817a",
    "runner": "orchestra",
    "signed_by": ""
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-29T08:28:24+00:00",
  "relationships": {},
  "revision": "sha256:9db0bf501515a9217e8f6b9b27ad8315e1e7904de5c7161a572b921f6f9881de",
  "subject": "hook-budget-plain"
}
---

F                                                                        [100%]
=================================== FAILURES ===================================
________ test_r12_plain_start_context_matches_claude_budget_and_content ________

repo = Project(project_root=PosixPath('/tmp/pytest-of-andrewyin/pytest-568/test_r12_plain_start_context_m0/repo'), store_path...ndrewyin/pytest-568/test_r12_plain_start_context_m0/repo/.canon'), binding=Binding(location='local', source='default'))
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x79da3785a3f0>
capsys = <_pytest.capture.CaptureFixture object at 0x79da378bc590>

    def test_r12_plain_start_context_matches_claude_budget_and_content(repo, monkeypatch, capsys):
        crowd_store(repo)
        claude = claude_context(repo, monkeypatch, capsys)
        plain = plain_context(repo, monkeypatch, capsys)
        assert plain == claude
>       assert len(plain) <= HOOK_BUDGET
E       AssertionError: assert 16801 <= 9000
E        +  where 16801 = len('This project keeps its state as canon records. Views are derived: edit records, not view output. Capture at the event... bytes; run `orchestra handoff` for the full handoff ...]\n\nOther views: `orchestra view plan|status|verification`.\n')

tests/test_hooks.py:480: AssertionError
=========================== short test summary info ============================
FAILED tests/test_hooks.py::test_r12_plain_start_context_matches_claude_budget_and_content
1 failed in 1.19s
warning: `VIRTUAL_ENV=/home/andrewyin/orchestra/.venv` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
