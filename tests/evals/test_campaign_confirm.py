from __future__ import annotations

import re
from pathlib import Path

from evals.seeded_defects.__main__ import main
from tests.evals.test_campaign import GOOD, TOKENS, Recording, cases, repo, saved

__all__ = ["cases", "repo"]


class Confirm:
    def __init__(self, *answers: bool) -> None:
        self.answers = list(answers)
        self.messages: list[str] = []
        self.calls_seen: list[int] = []
        self.run: Recording | None = None

    def __call__(self, message: str) -> bool:
        self.messages.append(message)
        if self.run is not None:
            self.calls_seen.append(len(self.run.claude_calls()))
        return self.answers.pop(0) if self.answers else True


def review(
    run: Recording, confirm: Confirm, repo: Path, cases: Path, campaign: Path, *extra: str
) -> int:
    confirm.run = run
    argv = [
        "review",
        "--model",
        "haiku",
        "--cases-dir",
        str(cases),
        "--repo",
        str(repo),
        "--campaign-dir",
        str(campaign),
        *extra,
    ]
    return main(argv, run=run, confirm=confirm)


def test_first_confirmation_before_any_call(repo: Path, cases: Path, tmp_path: Path) -> None:
    confirm = Confirm()
    run = Recording(default=GOOD)
    assert review(run, confirm, repo, cases, tmp_path / "camp") == 0
    assert confirm.calls_seen[:1] == [0]
    assert len(run.claude_calls()) == 9


def test_first_confirmation_message_contains_the_number_of_calls(
    repo: Path, cases: Path, tmp_path: Path
) -> None:
    confirm = Confirm()
    review(Recording(default=GOOD), confirm, repo, cases, tmp_path / "camp")
    assert re.search(r"\b9\b", "".join(confirm.messages[:1]))


def test_declined_first_confirmation_makes_zero_calls(
    repo: Path, cases: Path, tmp_path: Path
) -> None:
    confirm = Confirm(False)
    run = Recording(default=GOOD)
    campaign = tmp_path / "camp"
    assert review(run, confirm, repo, cases, campaign) != 0
    assert run.claude_calls() == []
    assert saved(campaign) == []
    assert len(confirm.messages) == 1


def test_second_confirmation_after_three_calls(repo: Path, cases: Path, tmp_path: Path) -> None:
    confirm = Confirm()
    run = Recording(default=GOOD)
    assert review(run, confirm, repo, cases, tmp_path / "camp") == 0
    assert len(confirm.messages) == 2
    assert confirm.calls_seen == [0, 3]
    assert len(run.claude_calls()) == 9


def test_second_confirmation_message_contains_the_projected_tokens(
    repo: Path, cases: Path, tmp_path: Path
) -> None:
    confirm = Confirm()
    review(Recording(default=GOOD), confirm, repo, cases, tmp_path / "camp")
    assert str(TOKENS * 9) in "".join(confirm.messages[1:])


def test_declined_second_confirmation_makes_exactly_three_calls_and_keeps_results(
    repo: Path, cases: Path, tmp_path: Path
) -> None:
    confirm = Confirm(True, False)
    run = Recording(default=GOOD)
    campaign = tmp_path / "camp"
    assert review(run, confirm, repo, cases, campaign) != 0
    assert len(run.claude_calls()) == 3
    assert len(saved(campaign)) == 3
    assert len(confirm.messages) == 2


def test_no_second_confirmation_when_three_or_fewer_calls_are_planned(
    repo: Path, cases: Path, tmp_path: Path
) -> None:
    confirm = Confirm()
    run = Recording(default=GOOD)
    assert review(run, confirm, repo, cases, tmp_path / "camp", "--cases", "c1") == 0
    assert len(confirm.messages) == 1
    assert len(run.claude_calls()) == 3


def test_resumed_run_counts_its_own_calls_for_the_second_confirmation(
    repo: Path, cases: Path, tmp_path: Path
) -> None:
    campaign = tmp_path / "camp"
    review(Recording(default=GOOD), Confirm(True, False), repo, cases, campaign)
    confirm = Confirm()
    run = Recording(default=GOOD)
    assert review(run, confirm, repo, cases, campaign) == 0
    assert re.search(r"\b6\b", "".join(confirm.messages[:1]))
    assert confirm.calls_seen == [0, 3]
    assert str(TOKENS * 6) in "".join(confirm.messages[1:])
    assert len(run.claude_calls()) == 6
