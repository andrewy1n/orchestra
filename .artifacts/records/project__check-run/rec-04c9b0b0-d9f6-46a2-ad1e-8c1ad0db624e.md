---
{
  "base_kind": "event",
  "id": "rec-04c9b0b0-d9f6-46a2-ad1e-8c1ad0db624e",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "plugin-root-and-cli-tier2",
    "duration_s": 400.000084,
    "effort": "packaging",
    "evidence_kind": "integration",
    "exit_code": 1,
    "failing_node_ids": "[\"tests/test_dashboard_journal.py::test_journal_detail_pager_pages_record_with_stub\"]",
    "method": "check",
    "output_sha256": "ae63435be13d70b6c2a2f190848222da7fa112c2f55d19f6526b0913af319661",
    "result": "fail",
    "revision": "8109e9aae50c888bd17a06bfb3b8f9e2f55665ab",
    "runner": "se-workflow",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "plugin-root-and-cli-tier2"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-14T08:59:22+00:00",
  "relationships": {},
  "revision": "sha256:72f4c75d9b97398ae5a4fe8237d8227329aa77c7421c5a8311357ca802e8ea19",
  "subject": "plugin-root-and-cli-tier2",
  "time": {
    "observed": "2026-10-14T08:59:22+00:00",
    "recorded": "2026-10-14T08:59:22+00:00"
  }
}
---

bringing up nodes...
bringing up nodes...

........................................................................ [  8%]
........................................................................ [ 16%]
........................................................................ [ 24%]
........................................................................ [ 33%]
........................................................................ [ 41%]
.........F.............................................................. [ 49%]
........................................................................ [ 58%]
........................................................................ [ 66%]
........................................................................ [ 74%]
........................................................................ [ 83%]
........................................................................ [ 91%]
........................................................................ [ 99%]
...                                                                      [100%]
=================================== FAILURES ===================================
_______________ test_journal_detail_pager_pages_record_with_stub _______________
[gw3] linux -- Python 3.13.3 /home/andrewyin/.cache/uv/builds-v0/.tmp4CCdxC/bin/python

journal_ui = PosixPath('/tmp/se-workflow-test-i16n7wuk')
tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-16/popen-gw3/test_journal_detail_pager_page0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7a6640f78750>

    def test_journal_detail_pager_pages_record_with_stub(journal_ui, tmp_path, monkeypatch):
        store = journal_ui
        script = tmp_path / "stub-pager"
        script.write_text(STUB_PAGER, encoding="utf-8")
        script.chmod(0o755)
        monkeypatch.setenv("PAGER", str(script))
        monkeypatch.setattr(pager.shutil, "which", lambda name: None)

        async def scenario(app, pilot):
            app.select_phase("alpha", "p-one")
            await pilot.pause()
            await pilot.press("J")
            screen = await _journal_shown(app, pilot)
            table = screen.query_one("#journal-table", JournalTable)
            item = next(i for i in table.items if i.id)
            table.move_cursor(row=table._keys.index(item.id))
            await pilot.pause()
            await pilot.press("enter")
            await _record_shown(app, pilot)
            monkeypatch.setattr(app, "suspend", lambda: __import__("contextlib").nullcontext())
            await pilot.press("o")
            await pilot.pause(0.3)
            out = script.with_suffix(".out")
            assert out.is_file(), "stub pager did not run"
            recorded_path_line, _, contents = out.read_text(encoding="utf-8").partition("\n")
            recorded = Path(recorded_path_line)
            assert recorded.suffix == ".md"
            assert ".artifacts" not in recorded.parts
            assert item.record_type in contents or item.subject in contents
            assert not recorded.exists()

>       _journal_run(store, scenario)

tests/test_dashboard_journal.py:877:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
tests/test_dashboard_journal.py:645: in _journal_run
    asyncio.run(go())
../.local/share/uv/python/cpython-3.13.3-linux-x86_64-gnu/lib/python3.13/asyncio/runners.py:195: in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
../.local/share/uv/python/cpython-3.13.3-linux-x86_64-gnu/lib/python3.13/asyncio/runners.py:118: in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../.local/share/uv/python/cpython-3.13.3-linux-x86_64-gnu/lib/python3.13/asyncio/base_events.py:719: in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
tests/test_dashboard_journal.py:643: in go
    await scenario(app, pilot)
tests/test_dashboard_journal.py:864: in scenario
    await _record_shown(app, pilot)
tests/test_dashboard_journal.py:658: in _record_shown
    await _until(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

pilot = <Pilot app=DashboardApp(title='DashboardApp', classes={'-dark-mode'}, pseudo_classes={'dark', 'focus'})>
condition = <function _record_shown.<locals>.<lambda> at 0x7a6641558d60>
timeout = 20.0

    async def _until(pilot, condition, timeout=20.0):
        deadline = time.monotonic() + timeout
        while not condition():
>           assert time.monotonic() < deadline, "condition not met in time"
E           AssertionError: condition not met in time
E           assert 5754.210946469 < 5754.20466848
E            +  where 5754.210946469 = <built-in function monotonic>()
E            +    where <built-in function monotonic> = time.monotonic

tests/test_dashboard_app.py:183: AssertionError
=========================== short test summary info ============================
FAILED tests/test_dashboard_journal.py::test_journal_detail_pager_pages_record_with_stub
1 failed, 866 passed in 386.23s (0:06:26)


## Failing node IDs

- tests/test_dashboard_journal.py::test_journal_detail_pager_pages_record_with_stub
