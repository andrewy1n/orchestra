from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest
from conftest import build_store

from evals.seeded_defects import scaffold_cmd
from evals.seeded_defects.cases import load_case_set
from evals.seeded_defects.trees import build_case_tree
from orchestra.canon.project import open_store

PHASE = "demo"
PASSING = "test -f feature.txt"
FAILING = "test -f missing.txt"
FILLER = "".join(f"line {n}\n" for n in range(20))
BASE_CALC = f"def add(a, b):\n    return a + b\n{FILLER}def sub(a, b):\n    return a - b\n"
LANDED_CALC = f"def add(a, b):\n    return b + a\n{FILLER}def sub(a, b):\n    return a + -b\n"
LANDED_TESTS = (
    "from src.calc import add, sub\n\n\n"
    "def test_add():\n    assert add(1, 2) == 3\n\n\n"
    "def test_sub():\n    assert sub(3, 1) == 2\n"
)
SECTIONS = {
    "score:specification": "## Requirements\n\nR1 adds.\n\n## Acceptance criteria\n\nA\n\n"
    "## Constraints\n\nC\n\n## Non-goals\n\nN\n\n## Invariants\n\nI\n\n## Assumptions\n\nS\n",
}


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


@dataclass
class Env:
    repo: Path
    landing: str
    store: Path
    cases: Path


@pytest.fixture
def env(tmp_path: Path) -> Env:
    repo = tmp_path / "source"
    (repo / "src").mkdir(parents=True)
    (repo / "tests").mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "t")
    (repo / "src" / "calc.py").write_text(BASE_CALC)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    (repo / "src" / "calc.py").write_text(LANDED_CALC)
    (repo / "tests" / "test_calc.py").write_text(LANDED_TESTS)
    (repo / "feature.txt").write_text("feature\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "landing")
    landing = git(repo, "rev-parse", "HEAD")
    store = build_store()
    project = open_store(store)
    project.create(
        record_type="score:effort", subject="e", payload={"goal": "g", "kind": "k"}, body=None
    )
    project.create(
        record_type="score:phase",
        subject=PHASE,
        payload={"title": "Demo", "ordinal": 1, "effort": "e"},
        body="## Problem\n\nP\n\n## Approach\n\nA\n\n## Exit criteria\n\nE\n",
    )
    project.create(
        record_type="score:work-item",
        subject="build",
        payload={
            "title": "Build it",
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "a",
            "effort": "e",
        },
        body="## Description\n\nBuild the calculator.\n",
    )
    for subject, command in (("passes", PASSING), ("fails", FAILING)):
        project.create(
            record_type="score:acceptance",
            subject=subject,
            payload={
                "method": "tdd",
                "phase": PHASE,
                "effort": "e",
                "verify_command": command,
                "criterion": f"criterion {subject}",
            },
            body=None,
        )
    project.create(
        record_type="score:specification",
        subject="spec",
        payload={"weight": "light", "phase": PHASE, "effort": "e", "requirements": ["R1"]},
        body=SECTIONS["score:specification"],
    )
    return Env(repo, landing, store, tmp_path / "cases")


def scaffold(env: Env, kind: str, **overrides: object) -> int:
    values: dict[str, object] = {
        "phase": PHASE,
        "commit": env.landing,
        "kind": kind,
        "defect_type": None,
        "hunk": 0,
        "test": None,
        "case_id": "case-1",
        "cases": env.cases,
        "repo": env.repo,
        "store_root": env.store,
        "expected_file": [],
        "expected_requirement_id": [],
    }
    values.update(overrides)
    args = argparse.Namespace(**values)
    return scaffold_cmd.run(args, lambda *a, **k: None, lambda _msg: True)  # pyright: ignore[reportArgumentType]


def tree_with(env: Env, patch: Path | None) -> Path:
    scratch = Path(tempfile.mkdtemp())
    return build_case_tree(env.repo, env.landing, patch, scratch / "tree")


def record_count(env: Env) -> int:
    return len(open_store(env.store, read_only=True).records())


def folder(env: Env) -> Path:
    return env.cases / "case-1"


def test_freezes_phase_records_as_reviewer_list(env: Env) -> None:
    assert scaffold(env, "control") == 0
    records = json.loads((folder(env) / "records.json").read_text())
    assert isinstance(records, list)
    by_type = {r["record_type"]: r for r in records}
    assert set(by_type) == {"work-item", "acceptance", "specification"}
    assert by_type["work-item"]["subject"] == "build"
    assert by_type["work-item"]["title"] == "Build it"
    assert "Build the calculator." in by_type["work-item"]["body"]
    assert "R1 adds." in by_type["specification"]["body"]


def test_acceptance_records_carry_verify_command(env: Env) -> None:
    assert scaffold(env, "control") == 0
    records = json.loads((folder(env) / "records.json").read_text())
    acceptances = {r["subject"]: r for r in records if r["record_type"] == "acceptance"}
    assert acceptances["passes"]["verify_command"] == PASSING
    assert acceptances["passes"]["criterion"] == "criterion passes"


def test_reverted_change_patch_reverses_one_landed_hunk(env: Env) -> None:
    assert scaffold(env, "synthetic-defect", defect_type="reverted-change", hunk=0) == 0
    patch = folder(env) / "defect.patch"
    assert patch.is_file()
    calc = (tree_with(env, patch) / "src" / "calc.py").read_text()
    assert "return a + b\n" in calc
    assert "return a + -b\n" in calc
    assert "return b + a\n" not in calc


def test_reverted_change_selects_hunk_by_index(env: Env) -> None:
    assert scaffold(env, "synthetic-defect", defect_type="reverted-change", hunk=1) == 0
    calc = (tree_with(env, folder(env) / "defect.patch") / "src" / "calc.py").read_text()
    assert "return b + a\n" in calc
    assert "return a - b\n" in calc


def test_reverted_change_never_touches_test_files(env: Env) -> None:
    assert scaffold(env, "synthetic-defect", defect_type="reverted-change", hunk=0) == 0
    patch = (folder(env) / "defect.patch").read_text()
    assert "tests/test_calc.py" not in patch


def test_removed_test_patch_deletes_one_test_function(env: Env) -> None:
    assert scaffold(env, "synthetic-defect", defect_type="removed-test", test="test_sub") == 0
    text = (tree_with(env, folder(env) / "defect.patch") / "tests" / "test_calc.py").read_text()
    assert "def test_sub" not in text
    assert "def test_add" in text


def test_control_writes_no_patch(env: Env) -> None:
    assert scaffold(env, "control") == 0
    assert (folder(env) / "case.json").is_file()
    assert not (folder(env) / "defect.patch").exists()


def test_baseline_maps_each_verify_command_to_clean_tree_result(env: Env) -> None:
    assert scaffold(env, "control") == 0
    baseline = json.loads((folder(env) / "baseline.json").read_text())
    assert baseline == {PASSING: "pass", FAILING: "fail"}


def test_case_json_records_diff_bytes_of_landed_diff(env: Env) -> None:
    assert scaffold(env, "control") == 0
    meta = json.loads((folder(env) / "case.json").read_text())
    expected = len(git(env.repo, "diff", "--binary", f"{env.landing}^", env.landing).encode())
    assert meta["diff_bytes"] == expected
    assert meta["phase"] == PHASE
    assert meta["revision"] == env.landing
    assert meta["kind"] == "control"


def test_case_json_records_defect_metadata(env: Env) -> None:
    assert (
        scaffold(
            env,
            "synthetic-defect",
            defect_type="reverted-change",
            expected_file=["src/calc.py"],
            expected_requirement_id=["R1"],
        )
        == 0
    )
    meta = json.loads((folder(env) / "case.json").read_text())
    assert meta["defect_type"] == "reverted-change"
    assert meta["expected_files"] == ["src/calc.py"]
    assert meta["expected_requirement_ids"] == ["R1"]


def test_scaffolded_defect_case_passes_load_case_set(env: Env) -> None:
    assert (
        scaffold(
            env, "synthetic-defect", defect_type="reverted-change", expected_file=["src/calc.py"]
        )
        == 0
    )
    cases = load_case_set(env.cases, env.repo)
    assert [c.id for c in cases] == ["case-1"]
    assert cases[0].patch is not None


def test_scaffolded_control_passes_load_case_set(env: Env) -> None:
    assert scaffold(env, "control") == 0
    cases = load_case_set(env.cases, env.repo)
    assert [c.kind for c in cases] == ["control"]


def test_scaffold_leaves_store_record_count_unchanged(env: Env) -> None:
    before = record_count(env)
    assert scaffold(env, "synthetic-defect", defect_type="removed-test", test="test_add") == 0
    assert (folder(env) / "records.json").is_file()
    assert record_count(env) == before
