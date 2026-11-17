from __future__ import annotations

import itertools
from pathlib import Path

from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.landing import (
    LandingPlace,
    belongs_to_phase,
    landing_place,
    proof_packet,
    task_branch,
    task_worktree,
)

HEAD = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
_CLOCK = itertools.count()


def _phase(body: str, effort: str = "code-quality") -> Record:
    return {
        "id": "<score:phase:p>",
        "record_type": "score:phase",
        "subject": "p",
        "payload": {"effort": effort},
        "lifecycle_state": "active",
        "relationships": {},
        "revision": "r0",
        "recorded_at": "2026-11-01T00:00:00Z",
        "body": body,
    }


def _packet(
    payload: JsonObject, *, phase: str = "p", corrects: str | None = None, name: str | None = None
) -> Record:
    n = next(_CLOCK)
    return {
        "id": name or f"<conductor:proof-packet:{n}>",
        "record_type": "conductor:proof-packet",
        "subject": phase,
        "payload": payload,
        "lifecycle_state": "recorded",
        "relationships": {"corrects": [corrects]} if corrects else {},
        "revision": f"r{n}",
        "recorded_at": f"2026-11-01T00:01:{n:02d}Z",
    }


def _place(tmp_path: Path, section: str) -> LandingPlace:
    place = landing_place(_phase(f"## Landing\n\n{section}\n"), tmp_path)
    assert place is not None
    return place


def test_r01_place_names_repo_worktree_branch_and_base(tmp_path: Path) -> None:
    body = "## Landing\n- Repo: /srv/r\n- Worktree: /srv/w\n- Branch: b\n- Base: dev\n"
    place = landing_place(_phase(body), tmp_path)
    assert place == LandingPlace(Path("/srv/r"), Path("/srv/w"), "b", "dev")


def test_r02_lines_set_each_part(tmp_path: Path) -> None:
    assert _place(tmp_path, "Repo: /srv/r").repo == Path("/srv/r")
    assert _place(tmp_path, "Worktree: /srv/w").worktree == Path("/srv/w")
    assert _place(tmp_path, "Branch: feat/x").branch == "feat/x"
    assert _place(tmp_path, "Base: dev").base == "dev"


def test_r02_grammar_allows_markers_backticks_and_any_case(tmp_path: Path) -> None:
    place = _place(tmp_path, "* `BRANCH`: nope\n- BRANCH: `feat/y`\n- bAsE:   `dev`  ")
    assert place.branch == "feat/y"
    assert place.base == "dev"


def test_r02_relative_paths_resolve_against_store_and_home_expands(tmp_path: Path) -> None:
    place = _place(tmp_path, "Repo: sub/repo\nWorktree: ~/wt")
    assert place.repo == tmp_path / "sub/repo"
    assert place.worktree == Path("~/wt").expanduser()
    assert _place(tmp_path, "Worktree: wt").worktree == tmp_path / "wt"


def test_r02_other_sections_are_ignored(tmp_path: Path) -> None:
    body = "## Landing\nBase: dev\n## Notes\nBranch: other\n"
    place = landing_place(_phase(body), tmp_path)
    assert place is not None
    assert (place.base, place.branch) == ("dev", "phase/p")


def test_r03_absent_repo_is_store_root(tmp_path: Path) -> None:
    assert _place(tmp_path, "Base: dev").repo == tmp_path


def test_r04_absent_worktree_is_repo_worktrees_phase(tmp_path: Path) -> None:
    assert _place(tmp_path, "Base: dev").worktree == tmp_path / ".worktrees" / "p"
    assert _place(tmp_path, "Repo: /srv/r").worktree == Path("/srv/r/.worktrees/p")


def test_r05_absent_branch_is_phase_slug_branch(tmp_path: Path) -> None:
    assert _place(tmp_path, "Base: dev").branch == "phase/p"


def test_r06_absent_base_is_main(tmp_path: Path) -> None:
    assert _place(tmp_path, "Branch: b").base == "main"


def test_r07_no_landing_section_has_no_place(tmp_path: Path) -> None:
    assert landing_place(_phase("## Problem\nRepo: /x\n"), tmp_path) is None
    assert landing_place(_phase(""), tmp_path) is None


def test_r07_heading_alone_gives_default_place(tmp_path: Path) -> None:
    place = landing_place(_phase("## Landing\n"), tmp_path)
    assert place == LandingPlace(tmp_path, tmp_path / ".worktrees/p", "phase/p", "main")


def test_r08_task_worktree_joins_phase_and_task(tmp_path: Path) -> None:
    place = _place(tmp_path, "Repo: /srv/r\nWorktree: /srv/custom")
    assert task_worktree(place, "p", "t") == Path("/srv/r/.worktrees/p--t")


def test_r09_task_branch_is_task_phase_task() -> None:
    assert task_branch("p", "t") == "task/p/t"


def test_r10_matching_phase_and_effort_belongs() -> None:
    phase = _phase("")
    packet = _packet({"phase": "p", "effort": "code-quality"})
    assert belongs_to_phase([packet], phase, packet)


def test_r10_missing_effort_belongs() -> None:
    packet = _packet({"phase": "p"})
    assert belongs_to_phase([packet], _phase(""), packet)


def test_r10_other_phase_does_not_belong() -> None:
    packet = _packet({"phase": "q", "effort": "code-quality"})
    assert not belongs_to_phase([packet], _phase(""), packet)


def test_r10_other_effort_does_not_belong() -> None:
    packet = _packet({"phase": "p", "effort": "other"})
    assert not belongs_to_phase([packet], _phase(""), packet)


def test_r10_corrected_packet_does_not_belong() -> None:
    old = _packet({"phase": "p"}, name="old")
    new = _packet({"phase": "p"}, corrects="old")
    assert not belongs_to_phase([old, new], _phase(""), old)
    assert belongs_to_phase([old, new], _phase(""), new)


def test_r11_packet_at_head_is_latest_matching(tmp_path: Path) -> None:
    older = _packet({"phase": "p", "revision": HEAD})
    newer = _packet({"phase": "p", "revision": HEAD})
    later_other = _packet({"phase": "p", "revision": "b" * 40})
    found = proof_packet([older, newer, later_other], _phase(""), HEAD)
    assert found is newer


def test_r11_older_revision_is_not_matched() -> None:
    packet = _packet({"phase": "p", "revision": "b" * 40})
    assert proof_packet([packet], _phase(""), HEAD) is None


def test_r11_seven_character_prefix_matches() -> None:
    packet = _packet({"phase": "p", "revision": HEAD[:7]})
    assert proof_packet([packet], _phase(""), HEAD) is packet
    assert proof_packet([_packet({"phase": "p", "revision": HEAD})], _phase(""), HEAD[:7])


def test_r11_non_belonging_packets_are_skipped() -> None:
    mine = _packet({"phase": "p", "revision": HEAD})
    other = _packet({"phase": "q", "revision": HEAD})
    wrong_effort = _packet({"phase": "p", "revision": HEAD, "effort": "x"})
    assert proof_packet([mine, other, wrong_effort], _phase(""), HEAD) is mine


def test_r12_no_head_gives_latest_belonging_packet() -> None:
    first = _packet({"phase": "p", "revision": HEAD})
    second = _packet({"phase": "p", "revision": "c" * 40})
    other = _packet({"phase": "q"})
    assert proof_packet([first, second, other], _phase("")) is second


def test_r12_no_belonging_packet_gives_none() -> None:
    assert proof_packet([_packet({"phase": "q"})], _phase("")) is None
