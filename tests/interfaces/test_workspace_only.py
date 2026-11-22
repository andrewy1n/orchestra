"""The views CLI and status command reach the store only through `Workspace.resolve`."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from interfaces.interfaces_support import invoke

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


WORKSPACE_MODULE = "orchestra/canon/workspace.py"
SCANNED_ROOTS = ("orchestra", "dashboard", "scripts")
RESOLVING_NAMES = {"resolve_location", "open_store", "bound_store_path"}
STORE_STRINGS = {"ORCHESTRA_STORE", "CANON_STORE", ".canon"}

STORE_RESOLUTION_EXEMPT: dict[str, str] = {
    "orchestra/canon/project.py": "implements open_store and the binding rule",
    "orchestra/canon/sqlite_backend.py": "derives the global database path",
    "orchestra/canon/store_commands.py": "store ensure bootstraps a store that does not exist yet",
    "orchestra/canon/cli.py": "canon init bootstraps stores and --store names a store directory",
    "orchestra/conductor/land_task.py": ".canon is a git pathspec, not store resolution",
    "orchestra/tuner/audit.py": ".canon is a path prefix, not store resolution",
    "scripts/api_schema.py": "builds an unbound Project for schema generation",
    "scripts/benchmark_cli.py": "builds a fixture store and env for child processes",
}


def store_resolution_hits(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in RESOLVING_NAMES:
            hits.append((node.lineno, node.id))
        elif isinstance(node, ast.Attribute) and node.attr in RESOLVING_NAMES:
            hits.append((node.lineno, node.attr))
        elif isinstance(node, ast.ImportFrom):
            hits.extend(
                (node.lineno, alias.name) for alias in node.names if alias.name in RESOLVING_NAMES
            )
        elif isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            if name == "Project":
                hits.append((node.lineno, "Project("))
        elif isinstance(node, ast.Constant) and node.value in STORE_STRINGS:
            hits.append((node.lineno, repr(node.value)))
    return sorted(set(hits))


def store_resolution_offenders() -> dict[str, list[tuple[int, str]]]:
    found: dict[str, list[tuple[int, str]]] = {}
    for root in SCANNED_ROOTS:
        for path in sorted((REPO_ROOT / root).rglob("*.py")):
            relative = path.relative_to(REPO_ROOT).as_posix()
            if relative == WORKSPACE_MODULE:
                continue
            hits = store_resolution_hits(path)
            if hits:
                found[relative] = hits
    return found


def test_workspace_only_scan_detects_each_resolution_form(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        "from orchestra.canon.project import open_store\n"
        "a = resolve_location(x)\n"
        "b = project.bound_store_path(x)\n"
        "c = Project(x)\n"
        "d = os.environ.get('ORCHESTRA_STORE')\n"
        "e = root / '.canon'\n"
        "f = root / 'other'\n",
        encoding="utf-8",
    )
    kinds = {kind for _, kind in store_resolution_hits(source)}
    assert kinds == {
        "open_store",
        "resolve_location",
        "bound_store_path",
        "Project(",
        "'ORCHESTRA_STORE'",
        "'.canon'",
    }


def test_workspace_only_no_module_outside_workspace_resolves_the_store() -> None:
    offenders = {
        relative: hits
        for relative, hits in store_resolution_offenders().items()
        if relative not in STORE_RESOLUTION_EXEMPT
    }
    assert offenders == {}


def test_workspace_only_exempt_list_only_names_current_offenders() -> None:
    current = store_resolution_offenders()
    stale = sorted(relative for relative in STORE_RESOLUTION_EXEMPT if relative not in current)
    assert stale == []
