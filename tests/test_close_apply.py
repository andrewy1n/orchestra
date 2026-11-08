from __future__ import annotations

from pathlib import Path

import pytest
from test_close import PHASE, Landed, _git, make_landed

from orchestra.conductor import close


@pytest.fixture
def merged(tmp_path: Path) -> Landed:
    return make_landed(tmp_path)


def _close(landed: Landed) -> close.CloseResult:
    return landed.close(landed.states("MERGED"))


def test_close_closes_phase(merged: Landed) -> None:
    _close(merged)

    assert merged.project.resolve("score:phase", PHASE)["lifecycle_state"] == "done"


def test_close_updates_effort_position(merged: Landed) -> None:
    before = merged.project.resolve("score:position", "alpha")

    _close(merged)

    after = merged.project.resolve("score:position", "alpha")
    assert (
        after["payload"]["position"]
        == f"{PHASE} merged as PR 7 ({merged.head[:12]}); phase closed."
    )
    assert after["payload"]["scope"] == before["payload"]["scope"]
    assert after["payload"]["effort"] == before["payload"]["effort"]


def test_close_removes_task_worktrees(merged: Landed) -> None:
    _close(merged)

    assert not merged.task_tree.exists()


def test_close_removes_phase_worktree(merged: Landed) -> None:
    _close(merged)

    assert not merged.phase_tree.exists()


def test_close_deletes_task_branches(merged: Landed) -> None:
    _close(merged)

    assert _git(merged.repo, "branch", "--list", f"task/{PHASE}/*") == ""


def test_close_deletes_phase_branch(merged: Landed) -> None:
    _close(merged)

    assert _git(merged.repo, "branch", "--list", f"phase/{PHASE}") == ""


def test_close_is_idempotent(merged: Landed) -> None:
    first = _close(merged)
    position = merged.project.resolve("score:position", "alpha")

    second = _close(merged)

    assert first.actions
    assert second.actions == ()
    assert "nothing left to do" in second.message
    assert merged.project.resolve("score:position", "alpha")["revision"] == position["revision"]


def test_a_refused_close_changes_nothing(merged: Landed) -> None:
    (merged.task_tree / "scratch.txt").write_text("x", encoding="utf-8")

    result = _close(merged)

    assert result.refusals
    assert result.actions == ()
    assert merged.phase_tree.is_dir()
    assert merged.task_tree.is_dir()
    assert _git(merged.repo, "branch", "--list", f"phase/{PHASE}") != ""
    assert merged.project.resolve("score:phase", PHASE)["lifecycle_state"] != "done"


def test_close_leaves_an_open_pull_request_alone(merged: Landed) -> None:
    result = merged.close(merged.states("OPEN"))

    assert result.actions == ()
    assert merged.phase_tree.is_dir()
    assert merged.project.resolve("score:phase", PHASE)["lifecycle_state"] != "done"


def test_close_all_closes_each_merged_phase_once(merged: Landed) -> None:
    states = merged.states("MERGED")

    first = close.close_all(merged.project, merged.repo, states)
    calls = states.calls
    second = close.close_all(merged.project, merged.repo, states)

    assert [item.phase for item in first if not isinstance(item, str)] == [PHASE]
    assert not merged.phase_tree.exists()
    assert second == ()
    assert states.calls == calls


def test_close_all_reports_a_failed_phase_and_goes_on(merged: Landed) -> None:
    class Broken:
        def pull_request_state(self, number: int) -> tuple[str, str]:
            raise close.CloseError(f"gh failed for {number}")

    results = close.close_all(merged.project, merged.repo, Broken())

    assert results == (f"{PHASE}: gh failed for 7",)
    assert merged.phase_tree.is_dir()


def test_close_cli_all_closes_and_reports(
    merged: Landed, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from orchestra.cli import main

    monkeypatch.setattr(close, "github_states", lambda _repo: merged.states("MERGED"))

    code = main(
        ["close", "--all", "--cwd", str(merged.repo), "--store", str(merged.project.project_root)]
    )

    assert code == 0
    assert f"closed phase {PHASE}" in capsys.readouterr().out
    assert not merged.phase_tree.exists()


def test_close_cli_needs_exactly_one_of_phase_and_all(
    merged: Landed, capsys: pytest.CaptureFixture[str]
) -> None:
    from orchestra.cli import main

    assert main(["close", "--cwd", str(merged.repo)]) == 2
    assert main(["close", "--phase", PHASE, "--all", "--cwd", str(merged.repo)]) == 2
    assert "exactly one of --phase and --all" in capsys.readouterr().err
