from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest
from conftest import git, make_git_repo

from orchestra import cli
from orchestra.canon.types import Record
from orchestra.cli import main as cli_main
from orchestra.conductor import suite

PHASE = "p1"


def write_policy(root: Path, mode: str, gate: str) -> None:
    (root / "orchestra.toml").write_text(
        '[verify.stages]\nphase = ["unit"]\n\n'
        '[verify.unit]\nrunner = ["python3", "-m", "pytest", "{tests}", "--junitxml={report}"]\n\n'
        "[suite]\n"
        f'mode = "{mode}"\n'
        'command = "true"\n'
        f'gate = "{gate}"\n',
        encoding="utf-8",
    )


def head_of(root: Path) -> str:
    return git(root, "rev-parse", "HEAD").stdout.strip()


def suite_run(head: str, result: str) -> Record:
    return {
        "id": f"rec-{head[:8]}-{result}",
        "record_type": "tuner:check-run",
        "subject": f"{PHASE}-suite",
        "payload": {
            "criterion_id": f"{PHASE}-suite",
            "evidence_kind": "integration",
            "revision": head,
            "result": result,
        },
        "lifecycle_state": "active",
        "relationships": {},
        "revision": "sha256:0",
        "recorded_at": "2026-11-07T00:00:00+00:00",
    }


def run_brief(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    root: Path,
    runs: Sequence[Record],
) -> tuple[int, str, str]:
    class _Project:
        def list(self, record_type: str) -> list[Record]:
            return list(runs) if record_type == "tuner:check-run" else []

    class _Location:
        def open(self) -> _Project:
            return _Project()

    monkeypatch.setattr(cli, "resolve_location", lambda *_args: _Location())
    code = cli.main(
        [
            "review-brief",
            "--cwd",
            str(root),
            "--base",
            "HEAD",
            "--phase-head",
            "HEAD",
            "--phase",
            PHASE,
        ]
    )
    out, err = capsys.readouterr()
    return code, out, err


@pytest.fixture
def repo() -> Path:
    return make_git_repo()


def test_brief_refuses_when_local_suite_has_no_check_run_at_head(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_policy(repo, "full", "required")
    code, out, err = run_brief(monkeypatch, capsys, repo, [])
    assert code == 2
    assert out == ""
    assert f"{PHASE}-suite" in err
    assert head_of(repo) in err


def test_brief_refuses_a_check_run_at_another_revision(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_policy(repo, "full", "advisory")
    code, _out, err = run_brief(monkeypatch, capsys, repo, [suite_run("0" * 40, "pass")])
    assert code == 2
    assert f"{PHASE}-suite" in err


def test_brief_refuses_a_failed_required_suite(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_policy(repo, "full", "required")
    code, out, err = run_brief(monkeypatch, capsys, repo, [suite_run(head_of(repo), "fail")])
    assert code == 2
    assert out == ""
    assert "did not pass" in err


def test_brief_builds_after_a_passing_required_suite(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_policy(repo, "full", "required")
    code, out, err = run_brief(monkeypatch, capsys, repo, [suite_run(head_of(repo), "pass")])
    assert code == 0, err
    assert out.startswith("# Reviewer brief")


def test_brief_builds_after_a_failed_advisory_suite(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_policy(repo, "full", "advisory")
    code, out, err = run_brief(monkeypatch, capsys, repo, [suite_run(head_of(repo), "fail")])
    assert code == 0, err
    assert out.startswith("# Reviewer brief")


@pytest.mark.parametrize(
    ("mode", "gate"),
    [("none", "required"), ("external", "required"), ("full", "deferred")],
)
def test_brief_needs_no_suite_run_when_policy_does_not_run_locally(
    mode: str,
    gate: str,
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_policy(repo, mode, gate)
    code, out, err = run_brief(monkeypatch, capsys, repo, [])
    assert code == 0, err
    assert out.startswith("# Reviewer brief")


def test_brief_check_reports_the_missing_subject() -> None:
    policy = suite.SuitePolicy(mode="full", command="true", gate="required")
    message = suite.suite_ready_for_review(policy, [], phase_slug=PHASE, phase_head="abc1234")
    assert message == f"no {PHASE}-suite check-run at abc1234"


@pytest.mark.parametrize(
    ("gate", "blocks_merge"),
    [("required", True), ("advisory", False), ("deferred", False)],
)
def test_required_advisory_deferred_merge_gate_matrix(gate: str, blocks_merge: bool) -> None:
    policy = suite.SuitePolicy(mode="full", command="true", gate=gate)

    assert policy.blocks_merge is blocks_merge


def test_review_brief_end_to_end(
    repo: Path,
    store: Path,
    cli: Callable[..., subprocess.CompletedProcess[str]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_policy(repo, "full", "required")
    argv = [
        "review-brief",
        "--cwd",
        str(repo),
        "--store",
        str(store),
        "--base",
        "HEAD",
        "--phase-head",
        "HEAD",
        "--phase",
        PHASE,
    ]
    assert cli_main(argv) == 2
    refused = capsys.readouterr()
    assert f"{PHASE}-suite" in refused.err
    assert refused.out == ""

    effort = cli(
        "create",
        "--type",
        "score:effort",
        "--subject",
        "workflow-loop",
        "--payload",
        json.dumps({"goal": "g", "kind": "deliver"}),
    )
    assert effort.returncode == 0, effort.stdout + effort.stderr
    created = cli(
        "create",
        "--type",
        "tuner:check-run",
        "--subject",
        f"{PHASE}-suite",
        "--payload",
        json.dumps(
            {
                "criterion_id": f"{PHASE}-suite",
                "revision": head_of(repo),
                "result": "pass",
                "effort": "workflow-loop",
                "method": "check",
                "signed_by": "",
                "evidence_kind": "integration",
                "runner": "orchestra",
            }
        ),
    )
    assert created.returncode == 0, created.stdout + created.stderr
    assert cli_main(argv) == 0
    assert capsys.readouterr().out.startswith("# Reviewer brief")
