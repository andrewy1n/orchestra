from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from evals.seeded_defects.__main__ import main
from evals.seeded_defects.cases import Case, CaseSetError, load_case_set
from orchestra.conductor.github_pr import GitHubGh
from orchestra.tools import Version
from orchestra.tools.testing import ScriptedRun

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # pyright: ignore[reportMissingImports]  # Pytest installs tomli on Python 3.10.

ROOT = Path(__file__).resolve().parents[2]

PATCH = (
    "diff --git a/a.txt b/a.txt\n"
    "--- a/a.txt\n"
    "+++ b/a.txt\n"
    "@@ -1,4 +1,4 @@\n"
    " one\n"
    "-two\n"
    "+TWO\n"
    " three\n"
    " four\n"
)
BAD_PATCH = (
    "diff --git a/a.txt b/a.txt\n"
    "--- a/a.txt\n"
    "+++ b/a.txt\n"
    "@@ -1,3 +1,3 @@\n"
    " nothing\n"
    "-matches\n"
    "+here\n"
    " at all\n"
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
    (path / "a.txt").write_text("one\ntwo\nthree\n")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "base")
    (path / "a.txt").write_text("one\ntwo\nthree\nfour\n")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "landing")
    return path, git(path, "rev-parse", "HEAD")


def write_case(
    root: Path,
    case_id: str,
    revision: str,
    *,
    kind: str = "synthetic-defect",
    defect_type: str | None = "reverted-change",
    patch: str | None = PATCH,
    expected_files: list[str] | None = None,
    expected_requirement_ids: list[str] | None = None,
    phase: str = "demo",
    records: bool = True,
) -> Path:
    folder = root / case_id
    folder.mkdir(parents=True)
    meta: dict[str, object] = {"phase": phase, "revision": revision, "kind": kind}
    if defect_type is not None:
        meta["defect_type"] = defect_type
    if expected_files is not None:
        meta["expected_files"] = expected_files
    if expected_requirement_ids is not None:
        meta["expected_requirement_ids"] = expected_requirement_ids
    (folder / "case.json").write_text(json.dumps(meta))
    if patch is not None:
        (folder / "defect.patch").write_text(patch)
    if records:
        (folder / "records.json").write_text("{}")
        (folder / "baseline.json").write_text("{}")
    return folder


def scripted() -> ScriptedRun:
    return ScriptedRun(GitHubGh, {}, Version(2, 50))


def test_case_has_source_phase_revision_kind(source: tuple[Path, str], tmp_path: Path) -> None:
    repo, rev = source
    cases = tmp_path / "cases"
    write_case(cases, "d1", rev, expected_files=["a.txt"])
    write_case(cases, "c1", rev, kind="control", defect_type=None, patch=None)
    write_case(
        cases,
        "r1",
        rev,
        kind="real-escape",
        defect_type=None,
        expected_requirement_ids=["R1"],
    )
    loaded = {c.id: c for c in load_case_set(cases, repo)}
    assert set(loaded) == {"d1", "c1", "r1"}
    assert loaded["d1"].phase == "demo"
    assert loaded["d1"].revision == rev
    assert {c.kind for c in loaded.values()} == {"synthetic-defect", "control", "real-escape"}
    with pytest.raises(FrozenInstanceError):
        loaded["d1"].phase = "other"  # pyright: ignore[reportAttributeAccessIssue]
    assert isinstance(loaded["d1"], Case)


def test_unknown_kind_rejected_source_phase_revision_kind(
    source: tuple[Path, str], tmp_path: Path
) -> None:
    repo, rev = source
    cases = tmp_path / "cases"
    write_case(cases, "bad", rev, kind="mystery", expected_files=["a.txt"])
    with pytest.raises(CaseSetError) as info:
        load_case_set(cases, repo)
    assert any("kind" in e for e in info.value.errors)


def test_defect_has_patch_and_expected_catch(source: tuple[Path, str], tmp_path: Path) -> None:
    repo, rev = source
    cases = tmp_path / "cases"
    write_case(cases, "d1", rev, expected_files=["a.txt"])
    (case,) = load_case_set(cases, repo)
    assert case.patch == cases / "d1" / "defect.patch"
    assert case.expected_files == frozenset({"a.txt"})


def test_defect_without_patch_rejected_defect_has_patch_and_expected_catch(
    source: tuple[Path, str], tmp_path: Path
) -> None:
    repo, rev = source
    cases = tmp_path / "cases"
    write_case(cases, "nopatch", rev, patch=None, expected_files=["a.txt"])
    with pytest.raises(CaseSetError) as info:
        load_case_set(cases, repo)
    assert any("nopatch" in e and "patch" in e for e in info.value.errors)


def test_defect_without_expected_catch_rejected_defect_has_patch_and_expected_catch(
    source: tuple[Path, str], tmp_path: Path
) -> None:
    repo, rev = source
    cases = tmp_path / "cases"
    write_case(cases, "nocatch", rev)
    with pytest.raises(CaseSetError) as info:
        load_case_set(cases, repo)
    assert any("nocatch" in e and "expected" in e for e in info.value.errors)


def test_expected_catch_sets(source: tuple[Path, str], tmp_path: Path) -> None:
    repo, rev = source
    cases = tmp_path / "cases"
    write_case(cases, "files", rev, expected_files=["a.txt", "b.txt"])
    write_case(cases, "reqs", rev, expected_requirement_ids=["R1", "R2"])
    write_case(cases, "both", rev, expected_files=["a.txt"], expected_requirement_ids=["R3"])
    loaded = {c.id: c for c in load_case_set(cases, repo)}
    assert loaded["files"].expected_files == frozenset({"a.txt", "b.txt"})
    assert loaded["files"].expected_requirement_ids == frozenset()
    assert loaded["reqs"].expected_files == frozenset()
    assert loaded["reqs"].expected_requirement_ids == frozenset({"R1", "R2"})
    assert loaded["both"].expected_files == frozenset({"a.txt"})
    assert loaded["both"].expected_requirement_ids == frozenset({"R3"})


def test_synthetic_defect_type(source: tuple[Path, str], tmp_path: Path) -> None:
    repo, rev = source
    cases = tmp_path / "cases"
    write_case(cases, "rc", rev, defect_type="reverted-change", expected_files=["a.txt"])
    write_case(cases, "rt", rev, defect_type="removed-test", expected_files=["a.txt"])
    loaded = {c.id: c for c in load_case_set(cases, repo)}
    assert loaded["rc"].defect_type == "reverted-change"
    assert loaded["rt"].defect_type == "removed-test"


def test_unknown_synthetic_defect_type_rejected_synthetic_defect_type(
    source: tuple[Path, str], tmp_path: Path
) -> None:
    repo, rev = source
    cases = tmp_path / "cases"
    write_case(cases, "x", rev, defect_type="bogus", expected_files=["a.txt"])
    with pytest.raises(CaseSetError) as info:
        load_case_set(cases, repo)
    assert any("defect type" in e for e in info.value.errors)


def test_synthetic_defect_without_type_rejected_synthetic_defect_type(
    source: tuple[Path, str], tmp_path: Path
) -> None:
    repo, rev = source
    cases = tmp_path / "cases"
    write_case(cases, "x", rev, defect_type=None, expected_files=["a.txt"])
    with pytest.raises(CaseSetError) as info:
        load_case_set(cases, repo)
    assert any("defect type" in e for e in info.value.errors)


def test_invalid_case_set_collects_every_error(source: tuple[Path, str], tmp_path: Path) -> None:
    repo, rev = source
    cases = tmp_path / "cases"
    write_case(cases, "badkind", rev, kind="mystery", expected_files=["a.txt"])
    write_case(cases, "badtype", rev, defect_type="bogus", expected_files=["a.txt"])
    write_case(cases, "norecords", rev, expected_files=["a.txt"], records=False)
    write_case(cases, "badpatch", rev, patch=BAD_PATCH, expected_files=["a.txt"])
    with pytest.raises(CaseSetError) as info:
        load_case_set(cases, repo)
    text = "\n".join(info.value.errors)
    for case_id in ("badkind", "badtype", "norecords", "badpatch"):
        assert case_id in text


def test_invalid_case_set_rejected_without_model_call(
    source: tuple[Path, str], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, rev = source
    cases = tmp_path / "cases"
    write_case(cases, "good", rev, expected_files=["a.txt"])
    write_case(cases, "badpatch", rev, patch=BAD_PATCH, expected_files=["a.txt"])
    run = scripted()
    code = main(
        ["validate", "--cases", str(cases), "--repo", str(repo)],
        run=run,
        confirm=lambda _message: True,
    )
    assert code == 1
    assert "badpatch" in capsys.readouterr().err
    assert run.calls == []


def test_valid_case_set_validate_makes_no_model_call(
    source: tuple[Path, str], tmp_path: Path
) -> None:
    repo, rev = source
    cases = tmp_path / "cases"
    write_case(cases, "good", rev, expected_files=["a.txt"])
    run = scripted()
    code = main(
        ["validate", "--cases", str(cases), "--repo", str(repo)],
        run=run,
        confirm=lambda _message: True,
    )
    assert code == 0
    assert run.calls == []


def test_evals_not_in_wheel_packages() -> None:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        data = tomllib.load(stream)
    packages: list[str] = []
    for section in (
        data.get("tool", {}).get("hatch", {}),
        data.get("tool", {}).get("setuptools", {}),
    ):
        packages.extend(section.get("packages", []))
    packages.extend(data.get("project", {}).get("packages", []))
    text = (ROOT / "pyproject.toml").read_text()
    assert "orchestra" in text
    assert not any(p == "evals" or p.startswith("evals.") for p in packages)
    assert "evals" not in _packages_list(text)


def _packages_list(text: str) -> list[str]:
    start = text.index("packages = [")
    end = text.index("]", start)
    return [line.strip().strip(",").strip('"') for line in text[start:end].splitlines()[1:]]
