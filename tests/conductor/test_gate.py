"""`orchestra gate` and the gate step of `orchestra land` over a temp store and a temp git repo."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from canon_support import create, make_project
from conductor_support import (
    EFFORT,
    HEAD,
    PHASE,
    Cli,
    Phase,
    _land_args,
    _landing,
    _packet,
    _review_repo_head,
    seed,
    write_policy,
)
from conftest import REPO_ROOT, git

from orchestra.canon.project import Project, open_store
from orchestra.canon.types import JsonObject, Record
from orchestra.canon.workspace import Workspace
from orchestra.cli import main as cli_main
from orchestra.conductor.landing import gate, landing

OTHER_HEAD = "b" * 40


def _orchestra(
    store: Path, *args: str, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in {"ORCHESTRA_STORE", "CANON_STORE"}}
    env["PYTHONPATH"] = os.pathsep.join(
        dict.fromkeys([str(REPO_ROOT), *filter(None, [env.get("PYTHONPATH")])])
    )
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", *args, "--store", str(store)],
        capture_output=True,
        text=True,
        cwd=str(cwd or store),
        env=env,
    )


@pytest.fixture
def phase(store: Path, cli: Cli) -> Phase:
    return seed(store, cli)


def test_gate_holds_when_every_term_is_met(phase: Phase) -> None:
    result = _orchestra(phase.store, "gate", PHASE)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "gate holds" in result.stdout
    assert phase.missing() == []


def test_gate_holds_reports_json(phase: Phase) -> None:
    result = _orchestra(phase.store, "gate", PHASE, "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {"phase": PHASE, "holds": True, "missing": []}


def test_gate_holds_with_required_suite_passing_at_head(phase: Phase) -> None:
    phase.set_suite_policy("required")
    phase.suite_run()
    assert _orchestra(phase.store, "gate", PHASE).returncode == 0


def test_gate_holds_with_failing_advisory_suite(phase: Phase) -> None:
    phase.set_suite_policy("advisory")
    phase.suite_run("fail")
    assert _orchestra(phase.store, "gate", PHASE).returncode == 0


def test_gate_holds_when_manual_check_is_signed(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, method="manual")
    assert _orchestra(store, "gate", PHASE).returncode == 0
    assert phase.missing() == []


def test_gate_holds_at_the_landing_worktree_head(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, review=False, runner_check=False)
    worktree = phase.repo / ".worktrees" / PHASE
    git(phase.repo, "worktree", "add", "-q", str(worktree), "phase/x")
    head = git(worktree, "rev-parse", "HEAD").stdout.strip()
    assert head not in (HEAD, OTHER_HEAD)
    phase.check_run(revision=head)
    phase.review(revision=head)
    assert _orchestra(store, "gate", PHASE).returncode == 0


def test_gate_names_missing_verification_task(store: Path, cli: Cli) -> None:
    seed(store, cli, verification="absent")
    result = _orchestra(store, "gate", PHASE)
    assert result.returncode == 1
    assert "verification-task-done: no verification task" in result.stdout


def test_gate_names_missing_verification_done(store: Path, cli: Cli) -> None:
    seed(store, cli, verification="in_progress")
    result = _orchestra(store, "gate", PHASE, "--json")
    assert result.returncode == 1
    assert json.loads(result.stdout)["missing"] == ["verification-task-done"]


def test_gate_names_missing_acceptance_pass(phase: Phase) -> None:
    phase.check_run("fail")
    result = _orchestra(phase.store, "gate", PHASE, "--json")
    assert result.returncode == 1
    assert json.loads(result.stdout)["missing"] == [f"acceptance-passes:{PHASE}-ac"]


def test_gate_names_missing_acceptance_check_run(store: Path, cli: Cli) -> None:
    seed(store, cli, runner_check=False)
    result = _orchestra(store, "gate", PHASE, "--json")
    assert result.returncode == 1
    assert json.loads(result.stdout)["missing"] == [
        f"acceptance-passes:{PHASE}-ac",
        f"acceptance-runner-at-head:{PHASE}-ac",
    ]


def test_gate_names_missing_runner_check_at_head(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, runner_check=False)
    phase.check_run(revision=OTHER_HEAD)
    result = _orchestra(store, "gate", PHASE, "--json")
    assert result.returncode == 1
    assert json.loads(result.stdout)["missing"] == [f"acceptance-runner-at-head:{PHASE}-ac"]


def test_gate_names_missing_runner_check_when_pass_is_manual_record(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, runner_check=False)
    phase.check_run(runner=False)
    result = _orchestra(store, "gate", PHASE, "--json")
    assert json.loads(result.stdout)["missing"] == [f"acceptance-runner-at-head:{PHASE}-ac"]


def test_gate_names_missing_manual_signature(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, method="manual", runner_check=False)
    phase.check_run(method="manual", runner=False, signed_by="")
    result = _orchestra(store, "gate", PHASE, "--json")
    assert result.returncode == 1
    assert json.loads(result.stdout)["missing"] == [f"manual-check-signed:{PHASE}-ac"]


def test_gate_names_missing_review(store: Path, cli: Cli) -> None:
    seed(store, cli, review=False)
    result = _orchestra(store, "gate", PHASE)
    assert result.returncode == 1
    assert "review-at-head" in result.stdout


def test_gate_names_missing_review_when_latest_review_fails(phase: Phase) -> None:
    phase.review("fail", revision=OTHER_HEAD)
    assert "review-at-head" in phase.missing()


def test_gate_names_missing_suite(phase: Phase) -> None:
    phase.set_suite_policy("required")
    result = _orchestra(phase.store, "gate", PHASE, "--json")
    assert result.returncode == 1
    assert json.loads(result.stdout)["missing"] == ["suite-at-head"]


def test_gate_names_missing_suite_at_a_stale_head(phase: Phase) -> None:
    phase.set_suite_policy("required")
    phase.suite_run(revision=OTHER_HEAD)
    assert phase.missing() == ["suite-at-head"]


@pytest.mark.parametrize(
    ("checked", "head", "expected"),
    [
        pytest.param(" abcdef0 ", "ABCDEF0123", True, id="whitespace-and-case"),
        pytest.param("abcd", "ABCD", True, id="exact-short"),
        pytest.param("abcdef0", "abcdef0123", True, id="seven-prefix"),
        pytest.param("abcdef0123", "abcdef0", True, id="reverse-seven-prefix"),
        pytest.param("abcdef01", "abcdef0123", True, id="longer-prefix"),
        pytest.param("abcdef0123", "abcdef01", True, id="reverse-longer-prefix"),
        pytest.param("abcdef", "abcdef0123", False, id="six-prefix"),
        pytest.param("", "abcdef0123", False, id="empty-checked"),
        pytest.param("abcdef0", "", False, id="empty-head"),
        pytest.param("abcdef0123", "ghijklmnop", False, id="unrelated"),
    ],
)
def test_gate_terms_revision_policy_matrix(
    phase: Phase,
    checked: str,
    head: str,
    expected: bool,
) -> None:
    phase.review(revision=head)
    phase.check_run(revision=checked)
    phase.set_suite_policy("required")
    phase.suite_run(revision=checked)

    terms = {term.name: term for term in gate.gate_terms(open_store(phase.store), PHASE)}

    assert terms[f"acceptance-runner-at-head:{PHASE}-ac"].holds is expected
    assert terms["suite-at-head"].holds is expected


def test_gate_names_every_missing_term_at_once(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, verification="planned", review=False, runner_check=False)
    phase.finding()
    result = _orchestra(store, "gate", PHASE, "--json")
    assert result.returncode == 1
    assert json.loads(result.stdout)["missing"] == [
        "verification-task-done",
        f"acceptance-passes:{PHASE}-ac",
        f"acceptance-runner-at-head:{PHASE}-ac",
        "review-at-head",
        "finding-needs-human:review-gate-phase-spec-gap",
    ]


def test_gate_names_missing_unknown_phase(phase: Phase) -> None:
    result = _orchestra(phase.store, "gate", "no-such-phase")
    assert result.returncode == 2
    assert "not found" in result.stderr


def test_gate_needs_human_finding_blocks_an_otherwise_green_gate(phase: Phase) -> None:
    assert _orchestra(phase.store, "gate", PHASE).returncode == 0
    phase.finding()
    result = _orchestra(phase.store, "gate", PHASE)
    assert result.returncode == 1
    assert "finding-needs-human:review-gate-phase-spec-gap" in result.stdout


def test_gate_needs_human_finding_clears_when_needs_is_none(phase: Phase) -> None:
    finding = phase.finding()
    assert _orchestra(phase.store, "gate", PHASE).returncode == 1
    result = phase.cli(
        "update",
        "--type",
        "tuner:finding",
        "--id",
        finding["id"],
        "--payload",
        json.dumps({"needs": "none"}),
        "--expected-revision",
        finding["revision"],
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert _orchestra(phase.store, "gate", PHASE).returncode == 0


def test_gate_needs_human_finding_ignores_needs_none(phase: Phase) -> None:
    phase.finding(needs="none")
    assert _orchestra(phase.store, "gate", PHASE).returncode == 0


def test_gate_needs_human_finding_ignores_other_efforts(phase: Phase) -> None:
    phase.create("score:effort", "other-effort", {"goal": "g", "kind": "deliver"})
    phase.create(
        "tuner:finding",
        "elsewhere",
        {
            "claim": "c",
            "basis": "b",
            "invalidated_when": "i",
            "effort": "other-effort",
            "needs": "human",
        },
        "## Evidence\n\ne\n\n## Consequence\n\nc\n\n## Follow-up\n\nf",
    )
    assert _orchestra(phase.store, "gate", PHASE).returncode == 0


def _worktree_phase(store: Path, cli: Cli, *landing_lines: str) -> tuple[Phase, Path, str]:
    phase = seed(
        store,
        cli,
        review=False,
        runner_check=False,
        landing_lines=landing_lines,
    )
    worktree = phase.repo / ".worktrees" / PHASE
    git(phase.repo, "worktree", "add", "-q", str(worktree), "phase/x")
    head = git(worktree, "rev-parse", "HEAD").stdout.strip()
    phase.check_run(revision=head)
    phase.review(revision=head)
    return phase, worktree, head


def _commit(worktree: Path, relative: str) -> None:
    path = worktree / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("changed\n")
    git(worktree, "add", "-A", "--", ".")
    git(worktree, "commit", "-qm", f"touch {relative}")


def test_canon_only_commit_after_review_holds(store: Path, cli: Cli) -> None:
    phase, worktree, _ = _worktree_phase(store, cli)
    _commit(worktree, ".canon/config.json")
    assert phase.missing() == []
    assert _orchestra(store, "gate", PHASE).returncode == 0


def test_code_commit_after_review_refuses(store: Path, cli: Cli) -> None:
    phase, worktree, _ = _worktree_phase(store, cli)
    _commit(worktree, "src/new.py")
    _commit(worktree, ".canon/config.json")
    assert phase.missing() == ["head-descends-from-review"]
    assert "src/new.py" in phase.term("head-descends-from-review").detail
    result = _orchestra(store, "gate", PHASE)
    assert result.returncode == 1
    assert "head-descends-from-review" in result.stdout
    assert "src/new.py" in result.stdout


def test_head_that_does_not_descend_from_review_refuses(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, review=False, runner_check=False)
    worktree = phase.repo / ".worktrees" / PHASE
    git(phase.repo, "worktree", "add", "-q", str(worktree), "phase/x")
    git(phase.repo, "checkout", "-q", "--detach", "main")
    git(phase.repo, "commit", "--allow-empty", "-qm", "side")
    side = git(phase.repo, "rev-parse", "HEAD").stdout.strip()
    git(phase.repo, "checkout", "-q", "main")
    phase.review(revision=side)
    assert "does not descend" in phase.term("head-descends-from-review").detail
    assert not phase.term("head-descends-from-review").holds


def test_no_worktree_adds_no_descent_term(phase: Phase) -> None:
    names = [t.name for t in gate.gate_terms(open_store(phase.store), PHASE)]
    assert "head-descends-from-review" not in names


def test_latest_check_run_stable_and_skips_corrected(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, method="manual", runner_check=False)
    unsigned = phase.check_run(method="manual", runner=False, signed_by="")
    assert phase.missing() == [f"manual-check-signed:{PHASE}-ac"]
    result = phase.cli(
        "correct",
        "--type",
        "tuner:check-run",
        "--id",
        unsigned["id"],
        "--payload",
        json.dumps({"signed_by": "me"}),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert phase.missing() == []


def test_gate_head_evidence_rejects_six_character_prefix(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, runner_check=False)
    phase.check_run(revision=HEAD[:6])
    phase.set_suite_policy("required")
    phase.suite_run(revision=HEAD[:6])
    assert phase.missing() == [f"acceptance-runner-at-head:{PHASE}-ac", "suite-at-head"]


def test_gate_head_evidence_acceptance_subject_check_run_counts(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, runner_check=False)
    phase.check_run(criterion=phase.acceptance["subject"])
    assert phase.missing() == []


def test_gate_head_evidence_corrected_check_run_is_not_evidence(store: Path, cli: Cli) -> None:
    phase = seed(store, cli)
    failed = phase.check_run("fail")
    assert f"acceptance-passes:{PHASE}-ac" in phase.missing()
    result = phase.cli(
        "correct",
        "--type",
        "tuner:check-run",
        "--id",
        failed["id"],
        "--payload",
        json.dumps({"result": "pass"}),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert phase.missing() == []


def test_gate_head_evidence_suite_check_run_needs_integration_kind(phase: Phase) -> None:
    phase.set_suite_policy("required")
    phase.check_run(
        criterion=f"{PHASE}-suite", subject=f"{PHASE}-suite", evidence_kind="acceptance"
    )
    assert phase.missing() == ["suite-at-head"]


def test_gate_head_evidence_timestamp_tie_takes_the_later_written_record(
    store: Path, cli: Cli, monkeypatch: pytest.MonkeyPatch
) -> None:
    phase = seed(store, cli, runner_check=False)
    earlier = phase.check_run("fail")
    later = phase.check_run("pass")
    stamp = "2026-11-01T00:00:00Z"
    stored = {r["id"]: r for r in Workspace(root=store).open().records()}
    others = [r for rid, r in stored.items() if rid not in {earlier["id"], later["id"]}]
    tied = [
        {**stored[earlier["id"]], "id": "rec-zzzz", "recorded_at": stamp},
        {**stored[later["id"]], "id": "rec-aaaa", "recorded_at": stamp},
    ]
    records = [*others, *tied]

    monkeypatch.setattr(Project, "records", lambda _self: records)
    terms = {t.name: t for t in gate.gate_terms(open_store(store), PHASE)}
    assert terms[f"acceptance-passes:{PHASE}-ac"].holds


def test_verification_task_needs_depends_on(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, verification="absent")
    item = {"phase": PHASE, "kind": "deliver", "assignee": "agent", "effort": EFFORT}
    named = phase.create(
        "score:work-item", f"verify-{PHASE}", {"title": "verify", **item}, "## Description\n\nd"
    )
    phase.advance(named, "in_progress", "done")
    assert phase.term("verification-task-done").detail == "no verification task"
    closing = phase.create(
        "score:work-item",
        f"{PHASE}-closing",
        {"title": "close", "depends_on": [f"{PHASE}-impl", f"verify-{PHASE}"], **item},
        "## Description\n\nd",
    )
    assert phase.term("verification-task-done").detail == "verification task is not done"
    phase.advance(closing, "in_progress", "done")
    assert phase.term("verification-task-done").holds


def test_relative_worktree_resolves_like_repo(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, review=False, runner_check=False)
    worktree = phase.repo.parent / f"{phase.repo.name}-linked"
    git(phase.repo, "worktree", "add", "-q", str(worktree), "phase/x")
    head = git(worktree, "rev-parse", "HEAD").stdout.strip()
    phase.check_run(revision=head)
    phase.review(revision=head)
    relative = os.path.relpath(worktree, store)
    body = _landing(phase.repo, f"- Worktree: `{relative}`")
    record = next(
        r for r in json.loads(phase.cli("list", "--type", "score:phase").stdout)["records"]
    )
    result = phase.cli(
        "update",
        "--type",
        "score:phase",
        "--id",
        record["id"],
        "--body",
        body,
        "--expected-revision",
        record["revision"],
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert phase.term("head-descends-from-review").holds
    _commit(worktree, "src/new.py")
    assert not phase.term("head-descends-from-review").holds


def test_landing_parses_repo_and_worktree_lines() -> None:
    body = (
        "## Approach\n\nrepo: not this\n\n## Landing\n\n"
        "- Branch: `phase/x`\n"
        "- Repo: `/code/repo`\n"
        "- Worktree: `/code/repo/.worktrees/x`\n\n"
        "## Proof\n\nrepo: ignored\n"
    )
    spec = landing.parse_landing(body)
    assert spec.present
    assert spec.repo == "/code/repo"
    assert spec.worktree == "/code/repo/.worktrees/x"


def test_landing_is_absent_without_a_landing_section() -> None:
    spec = landing.parse_landing("## Approach\n\nrepo: `/code/repo`\n")
    assert not spec.present
    assert spec.repo == ""


def test_land_refuses_when_gate_fails_no_push(
    phase: Phase, capsys: pytest.CaptureFixture[str]
) -> None:
    _packet(phase)
    phase.finding()
    assert cli_main(_land_args(phase)) == 5
    assert "finding-needs-human" in capsys.readouterr().err


def test_land_refuses_with_each_missing_term_once(
    phase: Phase, capsys: pytest.CaptureFixture[str]
) -> None:
    _packet(phase)
    phase.check_run("fail")
    assert cli_main(_land_args(phase)) == 5
    assert capsys.readouterr().err.count(f"acceptance-passes:{PHASE}-ac") == 1


def test_land_cwd_refuses_code_commit_after_review(
    store: Path, cli: Cli, capsys: pytest.CaptureFixture[str]
) -> None:
    phase = seed(store, cli, review=False, runner_check=False, prose_landing=True)
    _review_repo_head(phase)
    _commit(phase.repo, "src/new.py")
    _packet(phase)
    assert cli_main(_land_args(phase)) == 5
    err = capsys.readouterr().err
    assert "head-descends-from-review" in err
    assert "src/new.py" in err


def test_gate_cwd_checks_that_head(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, review=False, runner_check=False, prose_landing=True)
    _review_repo_head(phase)
    args = ["gate", PHASE, "--cwd", str(phase.repo)]
    assert _orchestra(store, *args).returncode == 0
    _commit(phase.repo, "src/new.py")
    result = _orchestra(store, *args)
    assert result.returncode == 1
    assert "head-descends-from-review" in result.stdout
    assert "src/new.py" in result.stdout
    assert _orchestra(store, "gate", PHASE).returncode == 0


def test_gate_cwd_reads_suite_policy_from_that_worktree(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, review=False, runner_check=False, prose_landing=True)
    _review_repo_head(phase)
    args = ["gate", PHASE, "--cwd", str(phase.repo), "--json"]
    write_policy(phase.repo, mode="smoke", command="true", gate="required")
    result = _orchestra(store, *args)
    assert result.returncode == 1
    assert json.loads(result.stdout)["missing"] == ["suite-at-head"]
    assert _orchestra(store, "gate", PHASE).returncode == 0
    write_policy(phase.repo)
    phase.set_suite_policy("required")
    assert _orchestra(store, *args).returncode == 0
    assert _orchestra(store, "gate", PHASE).returncode == 1


def test_land_exits_2_for_an_unknown_phase(
    phase: Phase, capsys: pytest.CaptureFixture[str]
) -> None:
    args = _land_args(phase)
    args[2] = "no-such-phase"
    assert cli_main(args) == 2
    assert "not found" in capsys.readouterr().err


GOLDEN = Path(__file__).resolve().parent.parent / "fixtures" / "gate_terms_main.json"
R10_PHASE = "r10-phase"
R10_EFFORT = "r10-effort"
R10_OTHER_EFFORT = "r10-other"
MANUAL_DETAIL = "latest manual check-run has no signed_by"


class _Clock:
    def __init__(self) -> None:
        self.ticks = 0

    def __call__(self) -> str:
        self.ticks += 1
        return f"2030-01-01T00:{self.ticks // 60:02d}:{self.ticks % 60:02d}+00:00"


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    ticking = _Clock()
    monkeypatch.setattr("orchestra.canon.record.now", ticking)
    monkeypatch.setattr("orchestra.canon.project.now", ticking)
    yield


def _r10_project(root: Path) -> Project:
    project = make_project(root)
    for effort in (R10_EFFORT, R10_OTHER_EFFORT):
        create(project, "score:effort", effort, {"goal": "g", "kind": "deliver"})
    create(project, "score:phase", R10_PHASE, {"title": "p", "ordinal": 1, "effort": R10_EFFORT})
    return project


def _r10_acceptance(project: Project, subject: str) -> Record:
    return create(
        project,
        "score:acceptance",
        subject,
        {
            "criterion": "c",
            "method": "manual",
            "phase": R10_PHASE,
            "effort": R10_EFFORT,
            "verify_command": "true",
            "requirement": "R1",
        },
    )


def _r10_run(
    project: Project, acceptance: Record, *, signed_by: str = "", by_subject: bool = False
) -> Record:
    return create(
        project,
        "tuner:check-run",
        acceptance["subject"],
        {
            "criterion_id": acceptance["subject"] if by_subject else acceptance["id"],
            "revision": HEAD,
            "result": "pass",
            "effort": R10_EFFORT,
            "method": "manual",
            "signed_by": signed_by,
        },
    )


def _r10_finding(project: Project, subject: str, effort: str) -> Record:
    payload: JsonObject = {
        "claim": f"claim of {subject}",
        "basis": "observed",
        "invalidated_when": "human clears",
        "effort": effort,
        "needs": "human",
    }
    return create(project, "tuner:finding", subject, payload)


def _r10_gate_store(root: Path) -> Project:
    project = _r10_project(root)
    _r10_run(project, _r10_acceptance(project, "ac-unsigned"))
    unsigned_then_signed = _r10_acceptance(project, "ac-unsigned-then-signed")
    _r10_run(project, unsigned_then_signed)
    _r10_run(project, unsigned_then_signed, signed_by="me")
    signed_then_unsigned = _r10_acceptance(project, "ac-signed-then-unsigned")
    _r10_run(project, signed_then_unsigned, signed_by="me")
    _r10_run(project, signed_then_unsigned)
    corrected = _r10_acceptance(project, "ac-corrected")
    project.correct(_r10_run(project, corrected)["id"], payload={"result": "fail"})
    _r10_run(project, _r10_acceptance(project, "ac-by-subject"), by_subject=True)
    create(
        project,
        "score:continuity-question",
        R10_EFFORT,
        {"owner": "me", "blocking": True, "scope": "which way"},
    )
    _r10_finding(project, "needs-human-here", R10_EFFORT)
    _r10_finding(project, "needs-human-elsewhere", R10_OTHER_EFFORT)
    return project


def _r10_snapshot(root: Path) -> list[dict[str, object]]:
    terms = gate.gate_terms(open_store(root), R10_PHASE)
    families = [term.name.partition(":")[0] for term in terms]
    ordered = sorted(
        zip(terms, families, strict=True),
        key=lambda pair: (families.index(pair[1]), pair[0].name),
    )
    return [{"name": term.name, "holds": term.holds, "detail": term.detail} for term, _ in ordered]


def _r10_manual_term(root: Path, acceptance: Record) -> gate.Term:
    terms = {term.name: term for term in gate.gate_terms(open_store(root), R10_PHASE)}
    return terms[f"manual-check-signed:{acceptance['subject']}"]


def test_r10_gate_terms_equal_the_golden_terms(tmp_path: Path, clock: None) -> None:
    _r10_gate_store(tmp_path)

    assert _r10_snapshot(tmp_path) == json.loads(GOLDEN.read_text())


def test_r10_latest_unsigned_manual_run_names_the_unsigned_term(
    tmp_path: Path, clock: None
) -> None:
    project = _r10_project(tmp_path)
    acceptance = _r10_acceptance(project, "ac-one")
    _r10_run(project, acceptance)

    term = _r10_manual_term(tmp_path, acceptance)

    assert term == gate.Term("manual-check-signed:ac-one", False, MANUAL_DETAIL)


def test_r10_older_unsigned_run_followed_by_signed_run_holds(tmp_path: Path, clock: None) -> None:
    project = _r10_project(tmp_path)
    acceptance = _r10_acceptance(project, "ac-one")
    _r10_run(project, acceptance)
    _r10_run(project, acceptance, signed_by="me")

    term = _r10_manual_term(tmp_path, acceptance)

    assert term == gate.Term("manual-check-signed:ac-one", True, "")
