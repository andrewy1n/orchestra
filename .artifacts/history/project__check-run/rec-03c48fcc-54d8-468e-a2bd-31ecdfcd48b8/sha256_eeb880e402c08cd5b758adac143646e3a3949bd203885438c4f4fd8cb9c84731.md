---
{
  "base_kind": "event",
  "id": "rec-03c48fcc-54d8-468e-a2bd-31ecdfcd48b8",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "plugin-root-and-cli-tier2",
    "duration_s": 5552.964617,
    "effort": "packaging",
    "evidence_kind": "integration",
    "exit_code": 1,
    "failing_node_ids": "[\"tests/test_dashboard_journal.py::test_journal_detail_pager_pages_record_with_stub\"]",
    "method": "check",
    "output_sha256": "162b04aa4173d7d8c2e49c0143cd32c0ce7d86700e4741103a6f948a45e21048",
    "result": "fail",
    "revision": "269ab7bde409ee04e1d7fa5de38363d9acb46c1e",
    "runner": "se-workflow",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "plugin-root-and-cli-tier2"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-14T08:50:14+00:00",
  "relationships": {},
  "revision": "sha256:eeb880e402c08cd5b758adac143646e3a3949bd203885438c4f4fd8cb9c84731",
  "subject": "plugin-root-and-cli-tier2",
  "time": {
    "observed": "2026-10-14T08:50:14+00:00",
    "recorded": "2026-10-14T08:50:14+00:00"
  }
}
---

bringing up nodes...
bringing up nodes...

........................................................................ [  8%]
........................................................................ [ 16%]
........................................................................ [ 25%]
........................................................................ [ 33%]
......................................................................F. [ 41%]
........................................................................ [ 50%]
........................................................................ [ 58%]
........................................................................ [ 67%]
........................................................................ [ 75%]
........................................................................ [ 83%]
........................................................................ [ 92%]
..................................................................       [100%]
==================================== ERRORS ====================================
_______________ ERROR collecting tests/test_verify_authority.py ________________
ImportError while importing test module '/home/andrewyin/se-workflow--plugin-root-and-cli/tests/test_verify_authority.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
../.local/share/uv/python/cpython-3.13.3-linux-x86_64-gnu/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_verify_authority.py:19: in <module>
    import close_batch  # noqa: E402
    ^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'close_batch'
=================================== FAILURES ===================================
_______________ test_journal_detail_pager_pages_record_with_stub _______________
[gw3] linux -- Python 3.13.3 /home/andrewyin/.cache/uv/builds-v0/.tmpLQZ4MR/bin/python

journal_ui = PosixPath('/tmp/se-workflow-test-jcb7v1vl')
tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-15/popen-gw3/test_journal_detail_pager_page0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x726e18222b30>

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

pilot = <Pilot app=DashboardApp(title='DashboardApp', classes={'-dark-mode'}, pseudo_classes={'focus', 'dark'})>
condition = <function _record_shown.<locals>.<lambda> at 0x726dfb6b2980>
timeout = 20.0

    async def _until(pilot, condition, timeout=20.0):
        deadline = time.monotonic() + timeout
        while not condition():
>           assert time.monotonic() < deadline, "condition not met in time"
E           AssertionError: condition not met in time
E           assert 5239.017184562 < 5238.999509659
E            +  where 5239.017184562 = <built-in function monotonic>()
E            +    where <built-in function monotonic> = time.monotonic

tests/test_dashboard_app.py:183: AssertionError
=========================== short test summary info ============================
FAILED tests/test_dashboard_journal.py::test_journal_detail_pager_pages_record_with_stub
ERROR tests/test_verify_authority.py - ImportError while importing test modul...
1 failed, 857 passed, 1 error in 405.20s (0:06:45)


## Failing node IDs

- tests/test_dashboard_journal.py::test_journal_detail_pager_pages_record_with_stub
