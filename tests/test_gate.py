"""`orchestra gate` and `orchestra land` over a temp store and a temp git repo."""

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

from orchestra.conductor import gate

PHASE = "gate-phase"
EFFORT = "gate-effort"
HEAD = "a" * 40
OTHER_HEAD = "b" * 40
PHASE_BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n"
MERGE = "git merge --ff-only phase/x"

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
        path = self.store / ".canon" / "config.json"
        config = json.loads(path.read_text())
        config.setdefault("settings", {})["conductor"] = {
            "phase_gate": {"suite": {"mode": "smoke", "command": "true", "gate": gate_mode}}
        }
        path.write_text(json.dumps(config))

    def term(self, name: str) -> gate.Term:
        terms = {t.name: t for t in gate.gate_terms(self.store, PHASE)}
        assert name in terms, sorted(terms)
        return terms[name]

    def missing(self) -> list[str]:
        return [t.name for t in gate.missing_terms(gate.gate_terms(self.store, PHASE))]


def _code_repo() -> Path:
    repo = make_git_repo()
    git(repo, "branch", "-M", "main")
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
    landing_lines: tuple[str, ...] = (f"- merge: `{MERGE}`",),
    verification: str = "done",
    review: bool = True,
    runner_check: bool = True,
) -> Phase:
    repo = _code_repo()
    phase = Phase(store, cli, repo, {})
    phase.create("score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    phase.create(
        "score:phase",
        PHASE,
        {"title": PHASE, "ordinal": 1, "effort": EFFORT},
        _landing(repo, *landing_lines),
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


def test_land_runs_merge_after_gate_holds(phase: Phase) -> None:
    result = _orchestra(phase.store, "land", PHASE)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (phase.repo / "landed.txt").read_text() == "landed\n"
    assert "phase work" in git(phase.repo, "log", "-1", "--format=%s", "main").stdout


def test_land_runs_merge_after_gate_and_exits_with_its_code(store: Path, cli: Cli) -> None:
    seed(store, cli, landing_lines=("- merge: `echo merging; exit 7`",))
    result = _orchestra(store, "land", PHASE)
    assert result.returncode == 7
    assert "merging" in result.stdout


def test_land_runs_merge_in_the_landing_repo(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, landing_lines=("- merge: `pwd > where.txt`",))
    result = _orchestra(store, "land", PHASE)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (phase.repo / "where.txt").read_text().strip() == str(phase.repo.resolve())


def test_land_refuses_when_gate_fails(phase: Phase) -> None:
    phase.finding()
    result = _orchestra(phase.store, "land", PHASE)
    assert result.returncode == 1
    assert "finding-needs-human" in result.stderr
    assert not (phase.repo / "landed.txt").exists()


def test_land_refuses_when_gate_fails_and_runs_no_command(store: Path, cli: Cli) -> None:
    marker = store / "ran.txt"
    seed(store, cli, review=False, landing_lines=(f"- merge: `touch {marker}`",))
    result = _orchestra(store, "land", PHASE)
    assert result.returncode == 1
    assert "review-at-head" in result.stderr
    assert not marker.exists()


def test_land_refuses_when_gate_fails_names_the_missing_term_only_once(phase: Phase) -> None:
    phase.check_run("fail")
    result = _orchestra(phase.store, "land", PHASE)
    assert result.returncode == 1
    assert result.stderr.count(f"acceptance-passes:{PHASE}-ac") == 1


def test_land_exits_2_without_a_merge_line(store: Path, cli: Cli) -> None:
    seed(store, cli, landing_lines=("- suite: `true`",))
    result = _orchestra(store, "land", PHASE)
    assert result.returncode == 2
    assert "merge:" in result.stderr


def test_landing_merge_and_suite_lines_are_parsed() -> None:
    body = (
        "## Approach\n\nmerge: not this\n\n## Landing\n\n"
        "- Branch: `phase/x`\n"
        "- Repo: `/code/repo`\n"
        "- merge: `git merge --ff-only phase/x`\n"
        "suite: uv run pytest -q\n\n"
        "## Proof\n\nmerge: ignored\n"
    )
    landing = gate.parse_landing(body)
    assert landing.present
    assert landing.merge == "git merge --ff-only phase/x"
    assert landing.suite == "uv run pytest -q"
    assert landing.repo == "/code/repo"


def test_landing_merge_and_suite_lines_are_optional() -> None:
    landing = gate.parse_landing("## Landing\n\n- Branch: `phase/x`\n")
    assert landing.present
    assert landing.merge == ""
    assert landing.suite == ""


def test_landing_merge_and_suite_lines_absent_without_a_landing_section() -> None:
    landing = gate.parse_landing("## Approach\n\nmerge: `git merge x`\n")
    assert not landing.present
    assert landing.merge == ""


def test_landing_merge_and_suite_lines_keep_inner_backticks() -> None:
    landing = gate.parse_landing("## Landing\n\nmerge: `git merge $(echo `x`)`\n")
    assert landing.merge == "git merge $(echo `x`)"
