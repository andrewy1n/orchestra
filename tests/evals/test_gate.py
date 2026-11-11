from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import pytest

from evals.seeded_defects import gate_cmd

BREAK_PATCH = (
    "diff --git a/broken.flag b/broken.flag\n"
    "new file mode 100644\n"
    "--- /dev/null\n"
    "+++ b/broken.flag\n"
    "@@ -0,0 +1 @@\n"
    "+x\n"
)
BENIGN_PATCH = (
    "diff --git a/note.txt b/note.txt\n"
    "new file mode 100644\n"
    "--- /dev/null\n"
    "+++ b/note.txt\n"
    "@@ -0,0 +1 @@\n"
    "+x\n"
)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


@pytest.fixture
def source(tmp_path: Path) -> tuple[Path, str]:
    path = tmp_path / "source"
    path.mkdir()
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "t@example.com")
    git(path, "config", "user.name", "t")
    (path / "a.txt").write_text("one\n")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "base")
    (path / "b.txt").write_text("landed\n")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "landing")
    return path, git(path, "rev-parse", "HEAD")


def write_case(
    cases: Path,
    case_id: str,
    revision: str,
    patch: str,
    acceptances: list[dict[str, str]],
    baseline: dict[str, str],
) -> None:
    folder = cases / case_id
    folder.mkdir(parents=True)
    (folder / "case.json").write_text(
        json.dumps(
            {
                "phase": "p",
                "revision": revision,
                "kind": "synthetic-defect",
                "defect_type": "reverted-change",
                "expected_files": ["broken.flag"],
            }
        )
    )
    (folder / "defect.patch").write_text(patch)
    (folder / "records.json").write_text(json.dumps({"acceptances": acceptances}))
    (folder / "baseline.json").write_text(json.dumps(baseline))


def run_gate(cases: Path, repo: Path, campaign: Path) -> int:
    args = argparse.Namespace(cases=cases, repo=repo, campaign_dir=campaign)
    return gate_cmd.run(args, lambda *a, **k: None, lambda _msg: True)  # pyright: ignore[reportArgumentType]


def report(campaign: Path, case_id: str) -> dict[str, object]:
    return json.loads((campaign / "gate" / f"{case_id}.json").read_text())


def test_runs_each_verify_command_once_on_patched_tree(
    tmp_path: Path, source: tuple[Path, str]
) -> None:
    repo, landing = source
    counter = tmp_path / "count.txt"
    cmd_a = f"echo a >> {counter}; test ! -f broken.flag"
    cmd_b = f"echo b >> {counter}; test -f b.txt"
    cases = tmp_path / "cases"
    write_case(
        cases,
        "c1",
        landing,
        BREAK_PATCH,
        [
            {"subject": "A", "verify_command": cmd_a},
            {"subject": "B", "verify_command": cmd_b},
        ],
        {cmd_a: "pass", cmd_b: "pass"},
    )
    campaign = tmp_path / "campaign"

    assert run_gate(cases, repo, campaign) == 0

    assert sorted(counter.read_text().split()) == ["a", "b"]
    assert (campaign / "gate" / "c1.json").is_file()


def test_catch_when_a_command_fails(tmp_path: Path, source: tuple[Path, str]) -> None:
    repo, landing = source
    cmd = "test ! -f broken.flag"
    cases = tmp_path / "cases"
    write_case(
        cases, "hit", landing, BREAK_PATCH, [{"subject": "A", "verify_command": cmd}], {cmd: "pass"}
    )
    write_case(
        cases,
        "miss",
        landing,
        BENIGN_PATCH,
        [{"subject": "A", "verify_command": cmd}],
        {cmd: "pass"},
    )
    campaign = tmp_path / "campaign"

    assert run_gate(cases, repo, campaign) == 0

    assert report(campaign, "hit")["caught"] is True
    assert report(campaign, "miss")["caught"] is False


def test_catch_ignores_a_command_that_already_fails_in_baseline(
    tmp_path: Path, source: tuple[Path, str]
) -> None:
    repo, landing = source
    cmd = "test -f never-there.txt"
    cases = tmp_path / "cases"
    write_case(
        cases, "c1", landing, BREAK_PATCH, [{"subject": "A", "verify_command": cmd}], {cmd: "fail"}
    )
    campaign = tmp_path / "campaign"

    assert run_gate(cases, repo, campaign) == 0

    assert report(campaign, "c1")["caught"] is False
