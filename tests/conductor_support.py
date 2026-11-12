from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import helpers as h
from canon_support import create, make_project, seed_effort
from conftest import git, make_git_repo

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor import close, gate
from orchestra.conductor.check import git_head, run_check

CLOSE_PHASE = "p1"


URL = "https://github.com/o/r/pull/7"


@dataclass
class FakeStates:
    state: str
    head_sha: str
    calls: int = 0

    def pull_request_state(self, number: int) -> tuple[str, str]:
        assert number == 7
        self.calls += 1
        return self.state, self.head_sha


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _commit(root: Path, name: str) -> str:
    (root / name).write_text(name, encoding="utf-8")
    _git(root, "add", name)
    _git(root, "commit", "-qm", name)
    return _git(root, "rev-parse", "HEAD")


@dataclass
class Landed:
    project: Project
    repo: Path
    head: str

    @property
    def phase_tree(self) -> Path:
        return self.repo / ".worktrees" / CLOSE_PHASE

    @property
    def task_tree(self) -> Path:
        return self.repo / ".worktrees" / f"{CLOSE_PHASE}--a"

    def states(self, state: str = "MERGED", head: str | None = None) -> FakeStates:
        return FakeStates(state, head or self.head)

    def close(self, states: FakeStates) -> close.CloseResult:
        return close.close_phase(self.project, self.repo, CLOSE_PHASE, states)


def make_landed(tmp_path: Path, *, shared_repo: bool = False) -> Landed:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    _commit(repo, "base.txt")
    _git(repo, "branch", f"phase/{CLOSE_PHASE}")
    _git(
        repo,
        "worktree",
        "add",
        "-q",
        str(repo / ".worktrees" / CLOSE_PHASE),
        f"phase/{CLOSE_PHASE}",
    )
    head = _commit(repo / ".worktrees" / CLOSE_PHASE, "work.txt")
    _git(repo, "branch", f"task/{CLOSE_PHASE}/a", f"phase/{CLOSE_PHASE}")
    _git(
        repo,
        "worktree",
        "add",
        "-q",
        str(repo / ".worktrees" / f"{CLOSE_PHASE}--a"),
        f"task/{CLOSE_PHASE}/a",
    )
    project = make_project(repo if shared_repo else tmp_path / "store")
    seed_effort(project, "alpha", CLOSE_PHASE)
    create(
        project,
        "conductor:landing",
        CLOSE_PHASE,
        {
            "phase": CLOSE_PHASE,
            "effort": "alpha",
            "number": 7,
            "url": URL,
            "head_sha": head,
            "result": "success",
        },
    )
    return Landed(project, repo, head)


def _commit_all(store: Path, message: str = "seed") -> str:
    git(store, "add", "-A")
    git(store, "commit", "-qm", message)
    return git(store, "rev-parse", "HEAD").stdout.strip()


def _seed_acceptance(
    store: Path,
    cli,
    resolved_contract,
    *,
    subject: str,
    verify_command: str,
    method: str = "tdd",
    requirement: str = "R1",
    commit: bool = True,
    extra_payload: dict | None = None,
) -> dict:
    defs = h.record_defs_by_id(resolved_contract)
    phase_subject = f"phase-{subject}"
    h.create_generic_record(
        cli,
        defs,
        "score:phase",
        subject=phase_subject,
        extra_payload={"title": phase_subject, "ordinal": 1, "effort": "workflow-loop"},
    )
    extra = {
        "criterion": f"criterion for {subject}",
        "method": method,
        "phase": phase_subject,
        "effort": "workflow-loop",
        "verify_command": verify_command,
        "requirement": requirement,
        **(extra_payload or {}),
    }
    result = cli(
        "create",
        "--type",
        "score:acceptance",
        "--subject",
        subject,
        "--payload",
        json.dumps(extra),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    record = json.loads(result.stdout)["record"]
    if commit:
        _commit_all(store, f"seed {subject}")
    return record


PHASE = "gate-phase"


EFFORT = "gate-effort"


HEAD = "a" * 40


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


def _review_repo_head(phase: Phase) -> str:
    head = git_head(phase.repo)
    phase.check_run(revision=head)
    phase.review(revision=head)
    return head


PROBE = 'from pathlib import Path\n\ndef test_probe():\n    assert Path("flag.txt").read_text() == "yes"\n'


NODE = "test_probe.py::test_probe"


def _commit_probe(root: Path) -> None:
    subprocess.run(
        ["git", "-C", str(root), "add", "test_probe.py", "flag.txt", ".gitignore"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "test",
        ],
        check=True,
        capture_output=True,
    )


def setup_acceptance(
    root: Path,
    method: str,
    policy: str | None,
    *,
    frozen: bool = False,
    phase_policy: str | None = None,
) -> tuple[Project, Record]:
    project = make_project(root)
    seed_effort(project)
    if phase_policy is not None:
        phase = project.list("score:phase")[0]
        project.update(phase["id"], payload={"oracle_policy": phase_policy})
    (root / "test_probe.py").write_text(PROBE)
    (root / "flag.txt").write_text("no")
    (root / ".gitignore").write_text(".canon/\n.pytest_cache/\n__pycache__/\n")
    _commit_probe(root)
    payload: JsonObject = {
        "method": method,
        "phase": "p1",
        "effort": "alpha",
        "verify_command": f"{sys.executable} -m pytest {NODE} -q",
    }
    if policy is not None:
        payload["oracle_policy"] = policy
    if frozen:
        payload["test_ids"] = [NODE]
        payload["oracle_hashes"] = [
            "test_probe.py:sha256:" + hashlib.sha256(PROBE.encode()).hexdigest()
        ]
    acceptance = create(project, "score:acceptance", "probe", payload)
    return project, acceptance


def run_acceptance(project: Project, acceptance: Record) -> Record:
    outcome = run_check(
        acceptance_id=acceptance["id"], cwd=project.project_root, store_root=project.project_root
    )
    assert outcome.record is not None, outcome.message
    return outcome.record


def green(project: Project, acceptance: Record) -> Record:
    (project.project_root / "flag.txt").write_text("yes")
    _commit_probe(project.project_root)
    result = run_acceptance(project, acceptance)
    assert result["payload"]["result"] == "pass"
    return result


def close_request(acceptance: Record, passed: Record, red: Record | None = None) -> JsonObject:
    entry: JsonObject = {
        "criterion_id": acceptance["id"],
        "method": acceptance["payload"]["method"],
        "check_run_id": passed["id"],
        "result": "pass",
    }
    if red is not None:
        entry["red_check_run_id"] = red["id"]
        entry["revision"] = passed["payload"]["revision"]
    return {
        "subject": "probe",
        "effort": "alpha",
        "work_item_id": "probe-item",
        "transition": "done",
        "acceptance_ids": [acceptance["id"]],
        "criteria": [entry],
    }
