from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import build_store
from test_campaign import GOOD, PATCH, Recording, git, yes

from evals.seeded_defects.__main__ import main
from orchestra.canon.project import open_store

RECORDS = [
    {"record_type": "work-item", "subject": "wi-1", "title": "Add two", "body": "BODY"},
    {
        "record_type": "acceptance",
        "subject": "wi-1",
        "criterion": "C",
        "body": "",
        "verify_command": "test -f a.txt",
    },
]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "source"
    (path / "agents").mkdir(parents=True)
    (path / "orchestra" / "conductor").mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "t@example.com")
    git(path, "config", "user.name", "t")
    (path / "a.txt").write_text("one\n")
    (path / "agents" / "reviewer.md").write_text("prompt v1\n")
    (path / "orchestra" / "conductor" / "reviewer.py").write_text("X = 1\n")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "base")
    (path / "a.txt").write_text("one\ntwo\n")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "landing")
    return path


@pytest.fixture
def cases(tmp_path: Path, repo: Path) -> Path:
    path = tmp_path / "cases"
    for case_id, defect in (("c1", False), ("c2", True)):
        folder = path / case_id
        folder.mkdir(parents=True)
        meta: dict[str, object] = {
            "phase": "p1",
            "revision": git(repo, "rev-parse", "HEAD"),
            "kind": "synthetic-defect" if defect else "control",
        }
        if defect:
            meta |= {"defect_type": "reverted-change", "expected_files": ["a.txt"]}
            (folder / "defect.patch").write_text(PATCH)
        (folder / "case.json").write_text(json.dumps(meta))
        (folder / "records.json").write_text(json.dumps(RECORDS))
        (folder / "baseline.json").write_text(json.dumps({"test -f a.txt": "pass"}))
    return path


def gate(repo: Path, cases: Path, campaign: Path, run: Recording) -> int:
    argv = ["gate", "--cases", str(cases), "--repo", str(repo), "--campaign-dir", str(campaign)]
    return main(argv, run=run, confirm=yes)


def review(repo: Path, cases: Path, campaign: Path, run: Recording) -> int:
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
    ]
    return main(argv, run=run, confirm=yes)


def test_gate_alone_makes_no_model_call(repo: Path, cases: Path, tmp_path: Path) -> None:
    run = Recording()
    campaign = tmp_path / "camp"
    assert gate(repo, cases, campaign, run) == 0
    assert run.claude_calls() == []
    assert sorted(p.name for p in (campaign / "gate").glob("*.json")) == ["c1.json", "c2.json"]
    assert not (campaign / "calls").exists()


def test_review_without_model_fails(
    repo: Path, cases: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run = Recording()
    argv = ["review", "--cases-dir", str(cases), "--repo", str(repo)]
    argv += ["--campaign-dir", str(tmp_path / "camp")]
    with pytest.raises(SystemExit) as exc:
        main(argv, run=run, confirm=yes)
    assert exc.value.code == 2
    assert "--model" in capsys.readouterr().err
    assert run.claude_calls() == []
    assert not (tmp_path / "camp").exists()


def test_store_record_count_unchanged(
    repo: Path, cases: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = open_store(build_store())
    project.create(
        record_type="score:effort", subject="e", payload={"goal": "g", "kind": "k"}, body=None
    )
    before = len(project.records())
    one, two = tmp_path / "one", tmp_path / "two"
    assert (
        main(["validate", "--cases", str(cases), "--repo", str(repo)], run=Recording(), confirm=yes)
        == 0
    )
    assert gate(repo, cases, one, Recording()) == 0
    assert review(repo, cases, one, Recording(default=GOOD)) == 0
    assert gate(repo, cases, two, Recording()) == 0
    assert review(repo, cases, two, Recording(default=GOOD)) == 0
    assert (
        main(
            ["report", "--campaign-dir", str(one), "--cases-dir", str(cases)],
            run=Recording(),
            confirm=yes,
        )
        == 0
    )
    assert (
        main(
            ["compare", str(one), str(two), "--cases-dir", str(cases)], run=Recording(), confirm=yes
        )
        == 0
    )
    capsys.readouterr()
    assert len(project.records()) == before


def test_report_names_model_prompt_commit_case_set(
    repo: Path, cases: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    campaign = tmp_path / "camp"
    assert review(repo, cases, campaign, Recording(default=GOOD)) == 0
    saved = json.loads((campaign / "campaign.json").read_text())
    capsys.readouterr()
    argv = ["report", "--campaign-dir", str(campaign), "--cases-dir", str(cases)]
    assert main(argv, run=Recording(), confirm=yes) == 0
    out = capsys.readouterr().out
    assert "model: haiku" in out
    assert f"reviewer prompt commit: {saved['prompt_commit']}" in out
    assert f"case set hash: {saved['case_set_hash']}" in out


def test_report_incomplete_count_stays_first_line(
    repo: Path, cases: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    campaign = tmp_path / "camp"
    assert review(repo, cases, campaign, Recording(default=GOOD)) == 0
    target = campaign / "calls" / "c1-1.json"
    saved = json.loads(target.read_text())
    target.write_text(json.dumps({**saved, "incomplete": True}))
    capsys.readouterr()
    argv = ["report", "--campaign-dir", str(campaign), "--cases-dir", str(cases)]
    assert main(argv, run=Recording(), confirm=yes) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "incomplete calls: 1"
    assert lines[1] == "model: haiku"
