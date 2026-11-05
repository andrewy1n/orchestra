"""`orchestra gate` and the gate step of `orchestra land` over a temp store and a temp git repo."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import helpers as h
import pytest
from conftest import REPO_ROOT, git, make_git_repo

from orchestra.canon.types import Record
from orchestra.cli import main as cli_main
from orchestra.conductor import gate, land
from orchestra.conductor.check import git_head

PHASE = "gate-phase"
EFFORT = "gate-effort"
HEAD = "a" * 40
OTHER_HEAD = "b" * 40
PHASE_BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n"
POLICY = """[verify.stages]
task = ["unit"]

[verify.unit]
runner = ["python3", "-m", "pytest", "{{tests}}", "--junitxml={{report}}"]

[suite]
mode = "{mode}"
command = "{command}"
gate = "{gate}"
"""

Cli = Callable[..., subprocess.CompletedProcess[str]]


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


@dataclass
class Phase:
    store: Path
    cli: Cli
    repo: Path
    acceptance: dict

    def create(
        self,
        record_type: str,
        subject: str,
        payload: dict,
        body: str | None = None,
        *,
        earlier: bool = False,
    ) -> dict:
        args = [
            "create",
            "--type",
            record_type,
            "--subject",
            subject,
            "--payload",
            json.dumps(payload),
        ]
        if body is not None:
            args.extend(["--body", body])
        if earlier:
            return h.run_cli_48h_ago(self.store, *args)
        result = self.cli(*args)
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout)["record"]

    def advance(self, record: dict, *states: str) -> dict:
        for state in states:
            result = self.cli(
                "update",
                "--type",
                record["record_type"],
                "--id",
                record["id"],
                "--transition",
                state,
                "--expected-revision",
                record["revision"],
            )
            assert result.returncode == 0, result.stdout + result.stderr
            record = json.loads(result.stdout)["record"]
        return record

    def check_run(
        self,
        result: str = "pass",
        *,
        revision: str = HEAD,
        criterion: str | None = None,
        method: str = "check",
        runner: bool = True,
        signed_by: str = "",
        subject: str | None = None,
        evidence_kind: str | None = None,
        earlier: bool = False,
    ) -> dict:
        criterion = criterion or self.acceptance["id"]
        payload: dict[str, object] = {
            "criterion_id": criterion,
            "revision": revision,
            "result": result,
            "effort": EFFORT,
            "method": method,
            "signed_by": signed_by,
        }
        if runner:
            payload["runner"] = "orchestra"
        if evidence_kind:
            payload["evidence_kind"] = evidence_kind
        return self.create(
            "tuner:check-run",
            subject or self.acceptance["subject"],
            payload,
            earlier=earlier,
        )

    def review(self, result: str = "pass", revision: str = HEAD, *, earlier: bool = False) -> dict:
        return self.check_run(
            result,
            earlier=earlier,
            revision=revision,
            criterion=f"{PHASE}-review",
            method="review",
            runner=False,
            subject=f"{PHASE}-review",
            evidence_kind="review",
        )

    def suite_run(self, result: str = "pass", revision: str = HEAD) -> dict:
        return self.check_run(
            result,
            revision=revision,
            criterion=f"{PHASE}-suite",
            subject=f"{PHASE}-suite",
            evidence_kind="integration",
        )

    def finding(self, subject: str = "review-gate-phase-spec-gap", needs: str = "human") -> dict:
        return self.create(
            "tuner:finding",
            subject,
            {
                "claim": "spec-gap on gate-phase",
                "basis": "observed",
                "invalidated_when": "human clears",
                "effort": EFFORT,
                "needs": needs,
            },
            "## Evidence\n\ne\n\n## Consequence\n\nc\n\n## Follow-up\n\nf",
        )

    def set_suite_policy(self, gate_mode: str) -> None:
        write_policy(self.store, mode="smoke", command="true", gate=gate_mode)

    def term(self, name: str) -> gate.Term:
        terms = {t.name: t for t in gate.gate_terms(self.store, PHASE)}
        assert name in terms, sorted(terms)
        return terms[name]

    def missing(self) -> list[str]:
        return [t.name for t in gate.missing_terms(gate.gate_terms(self.store, PHASE))]


def write_policy(
    root: Path, *, mode: str = "none", command: str = "", gate: str = "required"
) -> None:
    (root / "orchestra.toml").write_text(POLICY.format(mode=mode, command=command, gate=gate))


PROSE_LANDING = PHASE_BODY + "\n## Landing\n\nMerge phase/x into main after the review passes.\n"


def _code_repo() -> Path:
    repo = make_git_repo()
    git(repo, "branch", "-M", "main")
    write_policy(repo)
    git(repo, "add", "orchestra.toml")
    git(repo, "commit", "-qm", "policy")
    git(repo, "checkout", "-qb", "phase/x")
    (repo / "landed.txt").write_text("landed\n")
    git(repo, "add", "landed.txt")
    git(repo, "commit", "-qm", "phase work")
    git(repo, "checkout", "-q", "main")
    return repo


def _landing(repo: Path, *lines: str) -> str:
    return PHASE_BODY + "\n## Landing\n\n" + "\n".join([f"- Repo: `{repo}`", *lines]) + "\n"


def seed(
    store: Path,
    cli: Cli,
    *,
    method: str = "check",
    landing_lines: tuple[str, ...] = (),
    prose_landing: bool = False,
    verification: str = "done",
    review: bool = True,
    runner_check: bool = True,
) -> Phase:
    write_policy(store)
    repo = _code_repo()
    phase = Phase(store, cli, repo, {})
    phase.create("score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    phase.create(
        "score:phase",
        PHASE,
        {"title": PHASE, "ordinal": 1, "effort": EFFORT},
        PROSE_LANDING if prose_landing else _landing(repo, *landing_lines),
    )
    item = {"phase": PHASE, "kind": "deliver", "assignee": "agent", "effort": EFFORT}
    impl = phase.create(
        "score:work-item", f"{PHASE}-impl", {"title": "impl", **item}, "## Description\n\nd"
    )
    phase.advance(impl, "in_progress", "done")
    if verification != "absent":
        verify = phase.create(
            "score:work-item",
            f"verify-{PHASE}",
            {"title": "verify", "depends_on": [f"{PHASE}-impl"], **item},
            "## Description\n\nd",
        )
        if verification == "done":
            phase.advance(verify, "in_progress", "done")
        elif verification == "in_progress":
            phase.advance(verify, "in_progress")
    phase.acceptance = phase.create(
        "score:acceptance",
        f"{PHASE}-ac",
        {
            "criterion": "c",
            "method": method,
            "phase": PHASE,
            "effort": EFFORT,
            "verify_command": "true",
            "requirement": "R1",
        },
    )
    if runner_check:
        phase.check_run(
            method=method,
            runner=method != "manual",
            signed_by="me" if method == "manual" else "",
            earlier=True,
        )
    if review:
        phase.review(earlier=True)
    return phase


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

    terms = {term.name: term for term in gate.gate_terms(phase.store, PHASE)}

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
    names = [t.name for t in gate.gate_terms(phase.store, PHASE)]
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


def test_latest_check_run_keeps_store_order_on_equal_timestamps() -> None:
    def run(record_id: str, result: str) -> Record:
        return {
            "id": record_id,
            "record_type": "tuner:check-run",
            "subject": "s",
            "lifecycle_state": "active",
            "relationships": {},
            "revision": "r",
            "recorded_at": "2026-11-01T00:00:00Z",
            "payload": {"result": result},
        }

    runs = [run("z", "fail"), run("a", "pass")]
    latest = gate._latest(runs)
    assert latest is not None
    assert latest["id"] == "a"


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
    landing = gate.parse_landing(body)
    assert landing.present
    assert landing.repo == "/code/repo"
    assert landing.worktree == "/code/repo/.worktrees/x"


def test_landing_is_absent_without_a_landing_section() -> None:
    landing = gate.parse_landing("## Approach\n\nrepo: `/code/repo`\n")
    assert not landing.present
    assert landing.repo == ""


@dataclass
class FakeAdapter:
    calls: list[land.LandRequest]

    def run(self, request: land.LandRequest) -> land.LandingResult:
        self.calls.append(request)
        return land.LandingResult("success", 7, "https://example.test/pull/7", HEAD, (), ())


def _land_args(phase: Phase) -> list[str]:
    return ["land", "--phase", PHASE, "--cwd", str(phase.repo), "--store", str(phase.store)]


def _packet(phase: Phase) -> None:
    phase.create(
        "conductor:proof-packet",
        PHASE,
        {
            "phase": PHASE,
            "effort": EFFORT,
            "revision": git_head(phase.repo),
            "base": "main",
            "kind": "claims",
        },
        "## Look\nl\n\n## Machine\nm\n\n## Attention\nnone\n\n## Diff\n1 file changed\n",
    )


@pytest.fixture
def adapter(monkeypatch: pytest.MonkeyPatch) -> FakeAdapter:
    fake = FakeAdapter([])

    def dispatch(root: Path, proof_packet: str, **kwargs: object) -> land.LandingResult:
        return fake.run(land.LandRequest(root, proof_packet, "main", "origin", 0, 0, {}))

    monkeypatch.setattr(land, "dispatch_land", dispatch)
    return fake


def _review_repo_head(phase: Phase) -> str:
    head = git_head(phase.repo)
    phase.check_run(revision=head)
    phase.review(revision=head)
    return head


def test_land_refuses_when_gate_fails_no_push(
    phase: Phase, adapter: FakeAdapter, capsys: pytest.CaptureFixture[str]
) -> None:
    _packet(phase)
    phase.finding()
    assert cli_main(_land_args(phase)) == 5
    assert "finding-needs-human" in capsys.readouterr().err
    assert adapter.calls == []


def test_land_refuses_with_each_missing_term_once(
    phase: Phase, adapter: FakeAdapter, capsys: pytest.CaptureFixture[str]
) -> None:
    _packet(phase)
    phase.check_run("fail")
    assert cli_main(_land_args(phase)) == 5
    assert capsys.readouterr().err.count(f"acceptance-passes:{PHASE}-ac") == 1
    assert adapter.calls == []


def test_land_runs_adapter_after_gate_holds(
    phase: Phase, adapter: FakeAdapter, capsys: pytest.CaptureFixture[str]
) -> None:
    _review_repo_head(phase)
    _packet(phase)
    assert cli_main(_land_args(phase)) == 0
    assert len(adapter.calls) == 1
    assert adapter.calls[0].root == phase.repo.resolve()
    assert adapter.calls[0].proof_packet.startswith("## Look")
    assert '"result": "success"' in capsys.readouterr().out


def test_land_cwd_refuses_code_commit_after_review(
    store: Path, cli: Cli, adapter: FakeAdapter, capsys: pytest.CaptureFixture[str]
) -> None:
    phase = seed(store, cli, review=False, runner_check=False, prose_landing=True)
    _review_repo_head(phase)
    _commit(phase.repo, "src/new.py")
    _packet(phase)
    assert cli_main(_land_args(phase)) == 5
    err = capsys.readouterr().err
    assert "head-descends-from-review" in err
    assert "src/new.py" in err
    assert adapter.calls == []


def test_land_cwd_proceeds_after_canon_only_commit(
    store: Path, cli: Cli, adapter: FakeAdapter
) -> None:
    phase = seed(store, cli, review=False, runner_check=False, prose_landing=True)
    _review_repo_head(phase)
    _commit(phase.repo, ".canon/config.json")
    _packet(phase)
    assert cli_main(_land_args(phase)) == 0
    assert len(adapter.calls) == 1


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
    phase: Phase, adapter: FakeAdapter, capsys: pytest.CaptureFixture[str]
) -> None:
    args = _land_args(phase)
    args[2] = "no-such-phase"
    assert cli_main(args) == 2
    assert "not found" in capsys.readouterr().err
    assert adapter.calls == []
