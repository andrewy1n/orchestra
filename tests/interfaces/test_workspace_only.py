"""The views CLI and status command reach the store only through `Workspace.resolve`."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from interfaces_support import invoke

REPO_ROOT = Path(__file__).resolve().parents[2]
VIEWS_MODULES = ("orchestra/views/cli.py", "orchestra/views/status.py")
FORBIDDEN_NAMES = {
    "resolve_location",
    "open_store",
    "Project",
    "bound_store_path",
    "StoreBindingError",
}
FORBIDDEN_MODULES = {"orchestra.canon.project", "orchestra.canon.store_location"}
STORE_ARGV = (
    ("handoff",),
    ("view", "plan"),
    ("view", "status"),
    ("brief", "a"),
    ("status",),
)
NO_STORE = "No artifact store for"


def _tree(relative: str) -> ast.Module:
    return ast.parse((REPO_ROOT / relative).read_text(encoding="utf-8"))


@pytest.mark.parametrize("relative", VIEWS_MODULES)
def test_views_module_uses_no_direct_store_access(relative: str) -> None:
    tree = _tree(relative)
    used = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    used |= {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    modules = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    }
    assert (used | imported) & FORBIDDEN_NAMES == set()
    assert modules & FORBIDDEN_MODULES == set()


@pytest.mark.parametrize("relative", VIEWS_MODULES)
def test_views_module_resolves_through_workspace_with_read_access(relative: str) -> None:
    tree = _tree(relative)
    resolves = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "resolve"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "Workspace"
    ]
    assert resolves
    reads = [
        node
        for call in resolves
        for node in ast.walk(call)
        if isinstance(node, ast.Attribute)
        and node.attr == "READ"
        and isinstance(node.value, ast.Name)
        and node.value.id == "Access"
    ]
    assert reads


@pytest.mark.parametrize("argv", STORE_ARGV, ids=lambda argv: "views-" + "_".join(argv))
def test_views_same_store_for_root_and_nested_start_directory(
    argv: tuple[str, ...], shared_world: Path
) -> None:
    nested = shared_world / "sub" / "deep"
    nested.mkdir(parents=True, exist_ok=True)
    at_root = invoke("orchestra", list(argv), shared_world)
    in_nested = invoke("orchestra", list(argv), nested)
    assert at_root.code == 0, at_root.err
    assert in_nested.code == 0, in_nested.err
    assert in_nested.out == at_root.out


def test_views_status_directory_argument_picks_the_same_store(
    shared_world: Path, bare_dir: Path
) -> None:
    nested = shared_world / "sub" / "deep"
    nested.mkdir(parents=True, exist_ok=True)
    expected = invoke("orchestra", ["status"], shared_world)
    result = invoke("orchestra", ["status", str(nested)], bare_dir)
    assert result.code == 0, result.err
    assert result.out == expected.out


@pytest.mark.parametrize("argv", STORE_ARGV, ids=lambda argv: "views-" + "_".join(argv))
def test_views_env_store_wins_over_the_start_directory(
    argv: tuple[str, ...],
    shared_world: Path,
    bare_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = invoke("orchestra", list(argv), shared_world)
    monkeypatch.setenv("ORCHESTRA_STORE", str(shared_world))
    result = invoke("orchestra", list(argv), bare_dir)
    assert result.code == 0, result.err
    assert result.out == expected.out


@pytest.mark.parametrize("argv", STORE_ARGV, ids=lambda argv: "views-" + "_".join(argv))
def test_views_bare_nested_dir_is_store_not_ready_with_every_searched_parent(
    argv: tuple[str, ...], bare_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ORCHESTRA_STORE", raising=False)
    nested = bare_dir / "one" / "two"
    nested.mkdir(parents=True)
    result = invoke("orchestra", list(argv), nested)
    text = result.out + result.err
    assert result.code == 1, text
    assert "store_not_ready" in text
    assert NO_STORE in text
    assert "searched" in text
    for searched in (nested, nested.parent, bare_dir):
        assert str(searched) in text
