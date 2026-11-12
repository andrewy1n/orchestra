import ast
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
TESTS = REPO / "tests"

ROOTS = {
    "orchestra.score": "score",
    "orchestra.conductor": "conductor",
    "orchestra.composer": "composer",
    "orchestra.stage": "stage",
    "installer": "installer",
}


def _root_of(name: str) -> str | None:
    for root in ROOTS:
        if name == root or name.startswith(root + "."):
            return ROOTS[root]
    return None


def _imported_roots(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
            if node.module == "orchestra":
                names += [f"orchestra.{alias.name}" for alias in node.names]
        else:
            continue
        for name in names:
            root = _root_of(name)
            if root:
                found.add(root)
    return found


def _modules() -> list[Path]:
    return sorted(TESTS.rglob("test_*.py"))


def _rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def _assert_in_place(root: str) -> None:
    misplaced = [
        _rel(path)
        for path in sorted(TESTS.glob("test_*.py"))
        if _imported_roots(path) == {root}
    ]
    assert not misplaced, f"modules importing only {root} belong under tests/{root}/: {misplaced}"


def test_score_modules_in_place():
    _assert_in_place("score")


def test_conductor_modules_in_place():
    _assert_in_place("conductor")


def test_composer_modules_in_place():
    _assert_in_place("composer")


def test_installer_modules_in_place():
    _assert_in_place("installer")


def test_multi_root_modules_stay():
    moved = [
        _rel(path)
        for path in _modules()
        if path.parent != TESTS and len(_imported_roots(path)) >= 2
    ]
    assert not moved, f"modules importing two or more roots must stay in tests/: {moved}"


def test_no_stage_directory():
    assert not (TESTS / "stage").exists()


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout


def _removed_paths() -> set[str]:
    base = _git("merge-base", "HEAD", "main").strip()
    removed: set[str] = set()
    for line in _git("diff", "--name-status", "-M", base).splitlines():
        fields = line.split("\t")
        if fields[0].startswith(("D", "R")):
            removed.add(fields[1])
    return removed


def _assert_stays(relpath: str) -> None:
    target = REPO / relpath
    assert target.exists(), f"{relpath} is missing"
    prefix = relpath if target.is_file() else relpath.rstrip("/") + "/"
    gone = sorted(p for p in _removed_paths() if p == prefix or p.startswith(prefix))
    assert not gone, f"deleted or renamed from {relpath}: {gone}"


def test_cli_packaging_stays():
    _assert_stays("tests/test_cli_packaging.py")


def test_wheel_contents_stays():
    _assert_stays("tests/test_wheel_contents.py")


def test_canon_tests_stay():
    _assert_stays("tests/canon")


def test_tuner_tests_stay():
    _assert_stays("tests/tuner")


def test_dashboard_tests_stay():
    _assert_stays("tests/dashboard")


def test_integration_tests_stay():
    _assert_stays("tests/integration")


def test_tools_tests_stay():
    _assert_stays("tests/tools")


def _normalize(command: str) -> str:
    command = command.strip()
    command = re.sub(r"^run:\s*", "", command)
    command = command.replace("-p no:cacheprovider", "")
    return " ".join(command.split())


def _pytest_commands(text: str) -> list[str]:
    return [
        _normalize(line)
        for line in text.splitlines()
        if "uv run pytest" in line
    ]


def _readme_testing_commands() -> list[str]:
    text = (REPO / "README.md").read_text(encoding="utf-8")
    block = text.split("Run the full suite as three pytest processes:", 1)[1]
    block = block.split("```", 2)[1]
    return _pytest_commands(block)


def test_ci_runs_readme_commands():
    ci = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    ci_commands = [c.removeprefix("- ").strip() for c in _pytest_commands(ci)]
    ci_commands = [_normalize(c.removeprefix("run:").strip()) for c in ci_commands]
    readme = _readme_testing_commands()
    assert len(readme) == 3
    assert ci_commands == readme
    ignores = {
        token
        for command in ci_commands
        for token in command.split()
        if token.startswith("--ignore")
    }
    assert ignores == {"--ignore=tests/canon", "--ignore=tests/tuner"}
