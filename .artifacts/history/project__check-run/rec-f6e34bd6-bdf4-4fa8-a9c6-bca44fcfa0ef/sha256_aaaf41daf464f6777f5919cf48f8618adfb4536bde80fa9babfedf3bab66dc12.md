---
{
  "base_kind": "event",
  "id": "rec-f6e34bd6-bdf4-4fa8-a9c6-bca44fcfa0ef",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "atomic-claims-suite",
    "duration_s": 330.270574,
    "effort": "workflow-loop",
    "evidence_kind": "integration",
    "exit_code": 1,
    "failing_node_ids": "[\"tests/test_assess_routing.py::test_verify_and_assess_are_separate_steps\", \"tests/test_assess_routing.py::test_routing_table_chooses_next_from_the_evidence\", \"tests/test_dashboard_app.py::test_detail_related_panel_is_hidden_without_related_records[size0]\", \"tests/test_dashboard_journal.py::test_journal_detail_pager_pages_record_with_stub\"]",
    "method": "check",
    "output_sha256": "cec518eb8eacc1419796d20c798233254c878dea37b04b5679abe73ae43148f6",
    "result": "fail",
    "revision": "50303893af61c747620551cd512239752b0528a1",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "atomic-claims-suite"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-16T19:37:52+00:00",
  "relationships": {},
  "revision": "sha256:aaaf41daf464f6777f5919cf48f8618adfb4536bde80fa9babfedf3bab66dc12",
  "subject": "atomic-claims-suite",
  "time": {
    "observed": "2026-10-16T19:37:52+00:00",
    "recorded": "2026-10-16T19:37:52+00:00"
  }
}
---

st_routing_table_chooses_next_from_the_evidence _______________
[gw0] linux -- Python 3.13.3 /home/andrewyin/.cache/uv/builds-v0/.tmpHHvR2V/bin/python

    def test_routing_table_chooses_next_from_the_evidence():
        text = _text("verify-work")
        assert "Choose the first `next` from the evidence." in text
        assert "Do not send every failure to execute." in text
        for cause, status, level, nxt in ROUTES:
>           assert cause in text
E           AssertionError: assert 'the criterion was not exercised' in '---\nname: verify-work\ndescription: >-\n  Captures aff check-run evidence, assesses what it means for\n  each requir...n  `in_progress` and use assessment `next` `execute` for that failure\n- Route `manual` criteria through `aff check`\n'

tests/test_assess_routing.py:89: AssertionError
______ test_detail_related_panel_is_hidden_without_related_records[size0] ______
[gw2] linux -- Python 3.13.3 /home/andrewyin/.cache/uv/builds-v0/.tmpHHvR2V/bin/python

detailed = (PosixPath('/tmp/se-workflow-test-f9rpte36'), {'id': 'rec-e449ad7f-bf6e-466b-80e0-a3ea07943070', 'record_type': 'proje...5-7f87-40bf-b3dc-bba87fe9c938', 'record_type': 'project:acceptance', 'base_kind': 'claim', 'subject': 'det-task', ...})
cli = <function cli.<locals>._run at 0x791201cab6a0>, size = (60, 40)

    @pytest.mark.parametrize("size", DETAIL_SIZES)
    def test_detail_related_panel_is_hidden_without_related_records(detailed, cli, size):
        store, task, _ = detailed

        async def scenario(app, pilot):
            table = app.query_one("#tasks")
            blocked = next(
                k.value for k in table.rows
                if "det-blocked" in str(table.get_row(k.value)[1]) or "title of det-blocked" in str(table.get_row(k.value)[1])
            )
            await _open_by_click(app, pilot, blocked)
            screen = await _shown(app, pilot)
            assert not screen.query_one("#related").display

>       _detail_run(store, size, scenario)

tests/test_dashboard_app.py:1342:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
tests/test_dashboard_app.py:1125: in _detail_run
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
tests/test_dashboard_app.py:1123: in go
    await scenario(app, pilot)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = DashboardApp(title='DashboardApp', classes={'-dark-mode'}, pseudo_classes={'dark', 'focus'})
pilot = <Pilot app=DashboardApp(title='DashboardApp', classes={'-dark-mode'}, pseudo_classes={'dark', 'focus'})>

    async def scenario(app, pilot):
        table = app.query_one("#tasks")
        blocked = next(
            k.value for k in table.rows
            if "det-blocked" in str(table.get_row(k.value)[1]) or "title of det-blocked" in str(table.get_row(k.value)[1])
        )
        await _open_by_click(app, pilot, blocked)
        screen = await _shown(app, pilot)
>       assert not screen.query_one("#related").display
E       AssertionError: assert not True
E        +  where True = Static(id='related', classes='panel').display
E        +    where Static(id='related', classes='panel') = query_one('#related')
E        +      where query_one = TaskDetailScreen().query_one

tests/test_dashboard_app.py:1340: AssertionError
_______________ test_journal_detail_pager_pages_record_with_stub _______________
[gw0] linux -- Python 3.13.3 /home/andrewyin/.cache/uv/builds-v0/.tmpHHvR2V/bin/python

journal_ui = PosixPath('/tmp/se-workflow-test-6ktnzbcg')
tmp_path = PosixPath('/tmp/pytest-of-andrewyin/pytest-170/popen-gw0/test_journal_detail_pager_page0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7c64497d9240>

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

tests/test_dashboard_journal.py:879:
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
tests/test_dashboard_journal.py:866: in scenario
    await _record_shown(app, pilot)
tests/test_dashboard_journal.py:659: in _record_shown
    await _until(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

pilot = <Pilot app=DashboardApp(title='DashboardApp', classes={'-dark-mode'}, pseudo_classes={'dark', 'focus'})>
condition = <function _record_shown.<locals>.<lambda> at 0x7c6448367920>
timeout = 40.0

    async def _until(pilot, condition, timeout=20.0):
        deadline = time.monotonic() + timeout
        while not condition():
>           assert time.monotonic() < deadline, "condition not met in time"
E           AssertionError: condition not met in time
E           assert 79491.314022679 < 79491.311196619
E            +  where 79491.314022679 = <built-in function monotonic>()
E            +    where <built-in function monotonic> = time.monotonic

tests/test_dashboard_app.py:183: AssertionError
=========================== short test summary info ============================
FAILED tests/test_assess_routing.py::test_verify_and_assess_are_separate_steps
FAILED tests/test_assess_routing.py::test_routing_table_chooses_next_from_the_evidence
FAILED tests/test_dashboard_app.py::test_detail_related_panel_is_hidden_without_related_records[size0]
FAILED tests/test_dashboard_journal.py::test_journal_detail_pager_pages_record_with_stub
4 failed, 903 passed in 328.94s (0:05:28)


## Failing node IDs

- tests/test_assess_routing.py::test_verify_and_assess_are_separate_steps
- tests/test_assess_routing.py::test_routing_table_chooses_next_from_the_evidence
- tests/test_dashboard_app.py::test_detail_related_panel_is_hidden_without_related_records[size0]
- tests/test_dashboard_journal.py::test_journal_detail_pager_pages_record_with_stub
