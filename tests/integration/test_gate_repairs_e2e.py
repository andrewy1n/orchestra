"""The gate repairs through the real entry points: `uv run canon` and `uv run orchestra`."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from conftest import REPO_ROOT, git, make_git_repo

PHASE = "e2e-phase"
EFFORT = "e2e-effort"
PHASE_BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n"
POLICY = """[verify.stages]
task = ["unit"]

[verify.unit]
runner = ["python3", "-m", "pytest", "{tests}", "--junitxml={report}"]

[land]
adapter = "none"
"""
SECTIONS = "## Evidence\n\ne\n\n## Consequence\n\nc\n\n## Follow-up\n\nf"


class World:
    def __init__(self, root: Path) -> None:
        self.store = make_git_repo()
        self.code = make_git_repo()
        self.env = {
            k: v
            for k, v in os.environ.items()
            if k not in {"ORCHESTRA_STORE", "CANON_STORE", "VIRTUAL_ENV"}
        }
        self.env["HOME"] = str(root / "home")
        (root / "home").mkdir()

    def run(
        self, tool: str, *args: str, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["uv", "run", "--quiet", "--project", str(REPO_ROOT), tool, *args],
            capture_output=True,
            text=True,
            cwd=str(cwd or self.store),
            env=self.env,
        )

    def canon(self, *args: str) -> dict:
        result = self.run("canon", *args)
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout)["record"] if args[0] != "init" else {}

    def create(
        self, record_type: str, subject: str, payload: dict, body: str | None = None
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
            args += ["--body", body]
        return self.canon(*args)

    def advance(self, record: dict, *states: str) -> None:
        for state in states:
            record = self.canon(
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


@pytest.fixture
def world(tmp_path: Path) -> World:
    world = World(tmp_path)
    world.canon("init", "--schemas", "score,conductor,tuner,composer")
    return world


def test_duplicate_canon_create_is_refused(world: World) -> None:
    payload = {"goal": "g", "kind": "deliver"}
    world.create("score:effort", EFFORT, payload)
    result = world.run(
        "canon",
        "create",
        "--type",
        "score:effort",
        "--subject",
        EFFORT,
        "--payload",
        json.dumps(payload),
    )
    assert result.returncode != 0
    assert "supersede" in result.stdout + result.stderr


def _seed_phase(world: World) -> tuple[Path, str]:
    code = world.code
    git(code, "branch", "-M", "main")
    git(code, "checkout", "-qb", "phase/x")
    (code / "landed.txt").write_text("landed\n")
    git(code, "add", "landed.txt")
    git(code, "commit", "-qm", "phase work")
    git(code, "checkout", "-q", "main")
    worktree = code / ".worktrees" / PHASE
    git(code, "worktree", "add", "-q", str(worktree), "phase/x")
    head = git(worktree, "rev-parse", "HEAD").stdout.strip()

    (world.store / "orchestra.toml").write_text(POLICY)
    landing = f"\n## Landing\n\n- Repo: `{code}`\n"
    world.create("score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    world.create(
        "score:phase", PHASE, {"title": PHASE, "ordinal": 1, "effort": EFFORT}, PHASE_BODY + landing
    )
    item = {"phase": PHASE, "kind": "deliver", "assignee": "agent", "effort": EFFORT}
    impl = world.create(
        "score:work-item",
        f"{PHASE}-impl",
        {"title": "Implement landing", **item},
        "## Description\n\nlanding-marker-text",
    )
    world.advance(impl, "in_progress", "done")
    verify = world.create(
        "score:work-item",
        f"verify-{PHASE}",
        {"title": "verify", "depends_on": [f"{PHASE}-impl"], **item},
        "## Description\n\nd",
    )
    world.advance(verify, "in_progress", "done")
    acceptance = world.create(
        "score:acceptance",
        f"{PHASE}-ac",
        {
            "criterion": "c",
            "method": "check",
            "phase": PHASE,
            "effort": EFFORT,
            "verify_command": "true",
            "requirement": "R1",
        },
    )
    check = world.run(
        "orchestra",
        "check",
        "--acceptance",
        acceptance["id"],
        "--cwd",
        str(worktree),
        "--store",
        str(world.store),
    )
    assert check.returncode == 0, check.stdout + check.stderr
    world.create(
        "tuner:check-run",
        f"{PHASE}-review",
        {
            "criterion_id": f"{PHASE}-review",
            "revision": head,
            "result": "pass",
            "effort": EFFORT,
            "method": "review",
            "signed_by": "",
            "evidence_kind": "review",
        },
    )
    return code, head


def test_land_refuses_while_a_needs_human_finding_is_open_then_proceeds(world: World) -> None:
    code, _ = _seed_phase(world)
    worktree = code / ".worktrees" / PHASE
    store = str(world.store)
    gate = world.run("orchestra", "gate", PHASE, "--store", store)
    assert gate.returncode == 0, gate.stdout + gate.stderr

    finding = world.create(
        "tuner:finding",
        "review-e2e-phase-spec-gap",
        {
            "claim": "spec-gap",
            "basis": "b",
            "invalidated_when": "human clears",
            "effort": EFFORT,
            "needs": "human",
        },
        SECTIONS,
    )
    land = ("orchestra", "land", "--phase", PHASE, "--cwd", str(worktree), "--store", store)
    refused = world.run(*land)
    assert refused.returncode == 1
    assert "finding-needs-human:review-e2e-phase-spec-gap" in refused.stderr
    assert '"op": "land"' not in refused.stdout

    world.canon(
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
    metadata = worktree / ".canon" / "note.json"
    metadata.parent.mkdir(exist_ok=True)
    metadata.write_text("{}\n")
    git(worktree, "add", "-A", "--", ".canon")
    git(worktree, "commit", "-qm", "chore(canon): record metadata")
    (worktree / "orchestra.toml").write_text(POLICY)
    world.create(
        "conductor:proof-packet",
        PHASE,
        {
            "phase": PHASE,
            "effort": EFFORT,
            "revision": git(worktree, "rev-parse", "HEAD").stdout.strip(),
            "base": "main",
            "kind": "claims",
        },
        "## Look\nl\n\n## Machine\nm\n\n## Attention\nnone\n\n## Diff\n1 file changed\n",
    )
    landed = world.run(*land)
    assert "missing" not in landed.stderr, landed.stdout + landed.stderr
    result = json.loads(landed.stdout)
    assert result["op"] == "land"
    assert result["result"] == "skipped"


def test_review_brief_reads_a_store_in_another_repo(world: World) -> None:
    code, _ = _seed_phase(world)
    result = world.run(
        "orchestra",
        "review-brief",
        "--base",
        "main",
        "--phase-head",
        "phase/x",
        "--store",
        str(world.store),
        cwd=code,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "landing-marker-text" in result.stdout
    assert "landed.txt" in result.stdout
