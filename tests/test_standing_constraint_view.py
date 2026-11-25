from __future__ import annotations

import itertools
import subprocess
from pathlib import Path

from orchestra.canon.types import JsonObject, Record
from orchestra.views.render import VERIFICATION, phase_head_of, render_view

PHASE = "refunds"
NAME = "stripe-sdk-isolation"
EVIDENCE = "refunds.py:3: import stripe"
_CLOCK = itertools.count()


def _record(
    record_type: str,
    subject: str,
    payload: JsonObject,
    state: str = "recorded",
    body: str | None = None,
) -> Record:
    n = next(_CLOCK)
    record: Record = {
        "id": f"<{record_type}:{subject}-{n}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": f"r{n}",
        "recorded_at": f"2026-11-01T00:00:{n:02d}Z",
    }
    if body is not None:
        record["body"] = body
    return record


def _requirement_records() -> list[Record]:
    acceptance = _record(
        "score:acceptance",
        "refund-api",
        {
            "phase": PHASE,
            "effort": "e",
            "requirement": "R1",
            "method": "check",
            "verify_command": "true",
        },
        "active",
    )
    run = _record(
        "tuner:check-run",
        "refund-api",
        {
            "criterion_id": acceptance["id"],
            "result": "pass",
            "revision": "abc",
            "method": "check",
            "signed_by": "",
        },
    )
    spec = _record(
        "score:specification",
        f"{PHASE}-spec",
        {"phase": PHASE, "requirements": ["R1"]},
        "active",
    )
    return [spec, acceptance, run]


def _constraint(name: str = NAME) -> Record:
    return _record(
        "score:standing-constraint",
        name,
        {"area": "payments", "rule": "Only billing adapters import Stripe.", "check": "true"},
        "active",
    )


def _design(*pinned: Record) -> Record:
    return _record(
        "score:design",
        f"{PHASE}-design",
        {"phase": PHASE, "effort": "e", "standing_constraints": [c["id"] for c in pinned]},
        "active",
    )


def _constraint_run(constraint: Record, result: str, body: str | None = None) -> Record:
    return _record(
        "tuner:check-run",
        f"{constraint['subject']}-check",
        {
            "criterion_id": f"standing-constraint:{constraint['id']}",
            "result": result,
            "revision": "abc",
            "method": "check",
            "runner": "orchestra",
            "effort": "e",
            "signed_by": "",
        },
        body=body,
    )


def _view(records: list[Record]) -> str:
    return render_view(VERIFICATION, records, head_of=lambda _phase: "abc")


def _block(text: str) -> str:
    assert "### Standing constraints\n" in text
    return text.split("### Standing constraints\n", 1)[1].split("\n###", 1)[0]


def test_violated_constraint_listed_beside_verified_requirement() -> None:
    constraint = _constraint()
    run = _constraint_run(constraint, "fail", EVIDENCE)
    text = _view([*_requirement_records(), constraint, _design(constraint), run])

    assert "- **R1**: verified" in text
    assert text.index("### Requirements") < text.index("### Standing constraints")
    block = _block(text)
    assert f"- **{NAME}** (payments): violated" in block
    assert constraint["id"] in block
    assert run["id"] in block
    assert EVIDENCE in block


def test_verified_constraint_shows_outcome_and_check_run() -> None:
    constraint = _constraint()
    run = _constraint_run(constraint, "pass")
    block = _block(_view([*_requirement_records(), constraint, _design(constraint), run]))

    assert f"- **{NAME}** (payments): verified" in block
    assert run["id"] in block


def test_pinned_constraint_without_applicable_check_run_reads_unverified() -> None:
    old = _constraint()
    current = _constraint()
    older_pass = _constraint_run(old, "pass")
    block = _block(_view([*_requirement_records(), old, current, _design(current), older_pass]))

    assert f"- **{NAME}** (payments): unverified" in block
    assert current["id"] in block
    assert older_pass["id"] not in block


def test_no_block_when_phase_pins_nothing() -> None:
    constraint = _constraint()
    text = _view([*_requirement_records(), constraint, _design()])

    assert "- **R1**: verified" in text
    assert "### Standing constraints" not in text


def test_superseded_declaration_shows_newer_version() -> None:
    old = _constraint()
    run = _constraint_run(old, "pass")
    old_inactive: Record = {**old, "lifecycle_state": "superseded"}
    newer = _constraint()
    block = _block(_view([*_requirement_records(), old_inactive, newer, _design(old), run]))

    assert f"- **{NAME}** (payments): verified" in block
    assert old["id"] in block
    assert f" _(newer version: {newer['id']})_" in block


def test_constraint_at_other_revision_reads_unverified_in_view() -> None:
    constraint = _constraint()
    run = _constraint_run(constraint, "pass")
    records = [*_requirement_records(), constraint, _design(constraint), run]

    at_a = _block(render_view(VERIFICATION, records, head_of=lambda _phase: "abc"))
    at_b = _block(render_view(VERIFICATION, records, head_of=lambda _phase: "def"))

    assert f"- **{NAME}** (payments): verified" in at_a
    assert run["id"] in at_a
    assert "abc" in at_a
    assert f"- **{NAME}** (payments): unverified" in at_b
    assert run["id"] not in at_b
    assert "def" in at_b


def test_head_is_not_resolved_when_no_constraint_is_pinned() -> None:
    calls: list[str] = []

    def head_of(phase: str) -> str | None:
        calls.append(phase)
        return "abc"

    render_view(VERIFICATION, [*_requirement_records(), _constraint()], head_of=head_of)

    assert calls == []


def test_head_is_resolved_for_the_phase_that_pins_constraints() -> None:
    constraint = _constraint()
    calls: list[str] = []

    def head_of(phase: str) -> str | None:
        calls.append(phase)
        return "abc"

    render_view(
        VERIFICATION, [*_requirement_records(), constraint, _design(constraint)], head_of=head_of
    )

    assert calls == [PHASE]


def _git(repo: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout.strip()


def test_phase_head_is_the_phase_branch_tip_not_the_checkout_head(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-b", "main")
    (tmp_path / "a.txt").write_text("a")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "base")
    _git(tmp_path, "checkout", "-b", f"phase/{PHASE}")
    (tmp_path / "b.txt").write_text("b")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "phase work")
    phase_tip = _git(tmp_path, "rev-parse", "HEAD")
    _git(tmp_path, "checkout", "main")
    phase = _record(
        "score:phase",
        PHASE,
        {"title": PHASE, "ordinal": 1, "effort": "e"},
        "active",
        "## Problem\nx\n",
    )

    head_of = phase_head_of([phase], tmp_path)

    assert head_of(PHASE) == phase_tip
    assert head_of(PHASE) != _git(tmp_path, "rev-parse", "HEAD")


def test_phase_head_is_none_before_the_phase_branch_exists(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-b", "main")
    (tmp_path / "a.txt").write_text("a")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "base")
    phase = _record(
        "score:phase",
        PHASE,
        {"title": PHASE, "ordinal": 1, "effort": "e"},
        "active",
        "## Problem\nx\n",
    )

    assert phase_head_of([phase], tmp_path)(PHASE) is None
