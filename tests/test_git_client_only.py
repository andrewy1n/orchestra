from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIT_CLIENT = ROOT / "orchestra" / "tools" / "git.py"


def _passes_rev_parse_head(call: ast.Call) -> bool:
    literals = {arg.value for arg in call.args if isinstance(arg, ast.Constant)}
    return {"rev-parse", "HEAD"} <= literals


def test_commit_reads_use_git_head() -> None:
    offenders = []
    for base in (ROOT / "orchestra", ROOT / "dashboard" / "backend"):
        for path in sorted(base.rglob("*.py")):
            if path == GIT_CLIENT:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and _passes_rev_parse_head(node):
                    offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert offenders == []


def _string_literals(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def test_root_reads_use_git_root() -> None:
    offenders = []
    for base in (ROOT / "orchestra", ROOT / "dashboard" / "backend"):
        for path in sorted(base.rglob("*.py")):
            if path == GIT_CLIENT:
                continue
            if "--show-toplevel" in _string_literals(path):
                offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def _defined_functions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


def _called_attributes(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }


def test_wave_and_close_use_primary_checkout() -> None:
    wave = ROOT / "orchestra" / "conductor" / "wave.py"
    close = ROOT / "orchestra" / "conductor" / "close.py"
    offenders = []
    for base in (ROOT / "orchestra", ROOT / "dashboard" / "backend"):
        for path in sorted(base.rglob("*.py")):
            if path == GIT_CLIENT:
                continue
            if any("--git-common-dir" in lit for lit in _string_literals(path)):
                offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []
    assert not {"repo_root", "worktree_root"} & _defined_functions(wave)
    assert "primary_checkout" not in _defined_functions(close)
    assert "primary_checkout" in _called_attributes(ROOT / "orchestra" / "cli.py")
    assert "primary_checkout" in _called_attributes(ROOT / "orchestra" / "stage" / "hooks.py")


GIT_SUBCOMMANDS = frozenset({"rev-parse", "merge-base"})


def _subcommand_calls(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and any(isinstance(arg, ast.Constant) and arg.value in GIT_SUBCOMMANDS for arg in node.args)
    ]


def _structural_offenders(root: Path) -> list[str]:
    offenders = []
    for base in (root / "orchestra", root / "dashboard" / "backend"):
        for path in sorted(base.rglob("*.py")):
            if path == root / "orchestra" / "tools" / "git.py":
                continue
            offenders.extend(f"{path.relative_to(root)}:{line}" for line in _subcommand_calls(path))
    return offenders


def test_structural_check_fails_on_seeded_call(tmp_path: Path) -> None:
    seeded = tmp_path / "orchestra" / "seeded.py"
    seeded.parent.mkdir(parents=True)
    seeded.write_text('git.run("rev-parse", "HEAD")\n', encoding="utf-8")
    assert _structural_offenders(tmp_path) == ["orchestra/seeded.py:1"]


def test_structural_check_passes_on_tree() -> None:
    assert _structural_offenders(ROOT) == []
