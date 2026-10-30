"""Storage callers must use a path-free backend contract."""

from __future__ import annotations

import ast
import importlib
import importlib.util
import inspect
import os
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, get_args, get_type_hints

import pytest

from orchestra.canon.config import new_config
from orchestra.canon.project import Project, open_store
from orchestra.canon.store import Store

ROOT = Path(__file__).resolve().parents[2]
FILE_BACKEND = frozenset(
    {"store.py", "oplog.py", "git_backend.py", "record_file.py", "paths.py"}
)
PATH_MEMBERS = frozenset({"records_dir", "history_dir", "log_dir", "schemas_dir"})
PATH_METHODS = frozenset(
    {
        "config_path",
        "snapshot_path",
        "record_path",
        "history_snapshot_path",
        "type_dir",
        "lock_path",
    }
)
IO_METHODS = frozenset(
    {
        "open",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "glob",
        "rglob",
        "iterdir",
        "mkdir",
        "unlink",
        "is_file",
        "is_dir",
        "exists",
        "stat",
    }
)


def _backend_module() -> ModuleType:
    assert importlib.util.find_spec("orchestra.canon.backend") is not None, (
        "R1: backend.py must define Backend"
    )
    return importlib.import_module("orchestra.canon.backend")


def _protocol() -> type:
    protocol = getattr(_backend_module(), "Backend", None)
    assert isinstance(protocol, type), "R1: Backend must be a protocol class"
    assert getattr(protocol, "_is_protocol", False), (
        "R1: Backend must derive from typing.Protocol"
    )
    return protocol


def _factory() -> Callable[..., Any]:
    for name in (
        "orchestra.canon.backend",
        "orchestra.canon.store",
        "orchestra.canon.project",
    ):
        if importlib.util.find_spec(name) is not None:
            factory = getattr(importlib.import_module(name), "open_backend", None)
            if callable(factory):
                return factory
    pytest.fail("R3/R4: open_backend must provide the configured storage backend")


def _methods(protocol: type) -> dict[str, Callable[..., Any]]:
    return {
        name: value
        for name, value in vars(protocol).items()
        if not name.startswith("_") and callable(value)
    }


def _storage_receiver(node: ast.expr) -> bool:
    return isinstance(node, ast.Name) and node.id in {
        "store",
        "backend",
        "target",
        "source",
        "destination",
    }


def test_backend_protocol_declares_operations_used_by_callers() -> None:
    protocol = _protocol()
    methods = _methods(protocol)
    assert methods, "R1: an empty protocol does not declare storage operations"
    used: set[str] = set()
    for path in (ROOT / "orchestra" / "canon").glob("*.py"):
        if path.name in FILE_BACKEND or path.name == "backend.py":
            continue
        tree = ast.parse(path.read_text())
        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            receivers = {
                arg.arg
                for arg in function.args.args
                if arg.annotation is not None
                and ast.unparse(arg.annotation) in {"Store", "Backend"}
            }
            for node in ast.walk(function):
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                    call = node.value.func
                    if isinstance(call, ast.Name) and call.id in {
                        "Store",
                        "open_backend",
                    }:
                        receivers.update(
                            target.id
                            for target in node.targets
                            if isinstance(target, ast.Name)
                        )
                    if isinstance(call, ast.Attribute) and call.attr == "_session":
                        for target in node.targets:
                            if (
                                isinstance(target, ast.Tuple)
                                and target.elts
                                and isinstance(target.elts[0], ast.Name)
                            ):
                                receivers.add(target.elts[0].id)
            for node in ast.walk(function):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in receivers
                ):
                    used.add(node.func.attr)
    assert used, "R1: the contract must have real storage callers"
    assert used <= methods.keys(), (
        f"R1: operations missing from Backend: {sorted(used - methods.keys())}"
    )


def test_file_store_conforms_to_backend_and_preserves_layout(tmp_path: Path) -> None:
    methods = _methods(_protocol())
    store = Store(tmp_path / ".canon")
    assert all(callable(getattr(store, name, None)) for name in methods), (
        "R2: Store must implement every Backend operation"
    )
    assert store.init(new_config(), {"alpha": '{"namespace":"alpha"}'}) == "initialized"
    record_id = store.new_id()
    record = {
        "id": record_id,
        "record_type": "alpha:task",
        "subject": "layout",
        "lifecycle_state": "planned",
        "recorded_at": "2026-10-30T00:00:00+00:00",
        "payload": {"title": "Layout"},
        "relationships": {},
        "body": "Body\n",
    }
    written = store.create_record(record)
    assert store.read_record("alpha:task", record_id) == written
    assert (store.root / "config.json").is_file()
    assert (
        store.root / "schemas" / "alpha.json"
    ).read_text() == '{"namespace":"alpha"}'
    assert (store.root / "records" / "alpha__task" / f"{record_id}.md").is_file()
    assert list((store.root / "log" / "alpha__task" / record_id).glob("*"))
    assert not list(store.root.rglob("*.tmp-*"))


def _spy_factory(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    factory = _factory()
    calls: list[Path] = []

    def spy(root: Path, *args: Any, **kwargs: Any) -> Any:
        calls.append(Path(root))
        return factory(root, *args, **kwargs)

    for module in list(sys.modules.values()):
        if module is not None and module.__name__.startswith(
            ("orchestra.", "dashboard.")
        ):
            for name, value in list(vars(module).items()):
                if value is factory:
                    monkeypatch.setattr(module, name, spy)
    return calls


def test_open_store_obtains_backend_from_factory(
    project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _spy_factory(monkeypatch)
    reopened = open_store(project.project_root)
    assert reopened.records() == []
    assert project.store_path in [path.resolve() for path in calls], (
        "R3: open_store and its reads must obtain the backend through open_backend"
    )


def test_missing_backend_key_selects_file_store(tmp_path: Path) -> None:
    root = tmp_path / ".canon"
    Store(root).init(new_config())
    assert "backend" not in Store(root).load_config()
    backend = _factory()(root)
    assert isinstance(backend, Store), (
        "R4: a config with no backend selects the existing file Store"
    )
    assert backend.load_config() == new_config()


def test_orchestra_store_creation_uses_backend_factory(
    repo: Path, site: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from orchestra import cli

    monkeypatch.setattr(cli, "STORE_SCHEMAS", ("alpha", "beta"))
    calls = _spy_factory(monkeypatch)
    assert cli.main(["store", "ensure", "--cwd", str(repo), "--json"]) == 0
    assert (repo / ".canon").resolve() in [path.resolve() for path in calls], (
        "R7: store creation must use open_backend"
    )
    assert open_store(repo).records() == []


def test_dashboard_lists_and_filters_records_through_project(
    project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    from dashboard.backend import store as dashboard_store

    first = project.create(
        record_type="alpha:task", subject="first", payload={"title": "First"}
    )
    project.create(
        record_type="alpha:task", subject="second", payload={"title": "Second"}
    )
    calls: list[Project] = []
    records = Project.records

    def spy(target: Project) -> list[dict[str, Any]]:
        calls.append(target)
        return records(target)

    monkeypatch.setattr(Project, "records", spy)
    rows = dashboard_store.list_records(
        project,
        "alpha:task",
        state="planned",
        subject="fir",
        payload={"title": "First"},
    )
    assert [row["id"] for row in rows] == [first["id"]]
    assert calls == [project], (
        "R8: dashboard record enumeration must go through Project.records"
    )


def _contains_path(annotation: Any) -> bool:
    if isinstance(annotation, type):
        return issubclass(annotation, (Path, os.PathLike))
    return any(_contains_path(arg) for arg in get_args(annotation))


def test_backend_signatures_never_accept_or_return_file_paths() -> None:
    protocol = _protocol()
    violations: list[str] = []
    for name, method in _methods(protocol).items():
        hints = get_type_hints(method)
        for parameter in inspect.signature(method).parameters.values():
            if parameter.name == "self":
                continue
            assert parameter.name in hints, (
                f"R6: annotate Backend.{name}.{parameter.name}"
            )
            if "path" in parameter.name or _contains_path(hints[parameter.name]):
                violations.append(f"{name}.{parameter.name}")
        assert "return" in hints, f"R6: annotate Backend.{name}'s result"
        if "path" in name or _contains_path(hints["return"]):
            violations.append(f"{name}.return")
    assert not violations, f"R6: file paths in Backend signatures: {violations}"


def _store_path(node: ast.AST, aliases: set[str]) -> bool:
    if isinstance(node, ast.Name):
        return node.id in aliases or node.id in {
            "store_root",
            "store_path",
            "history_root",
            "records_dir",
            "history_dir",
            "log_dir",
            "schemas_dir",
        }
    if isinstance(node, ast.Attribute):
        return node.attr in PATH_MEMBERS | {"store_path"} or (
            node.attr == "root" and _storage_receiver(node.value)
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _store_path(node.left, aliases) or (
            isinstance(node.right, ast.Constant) and node.right.value == ".canon"
        )
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in PATH_METHODS and _storage_receiver(node.func.value):
                return True
            if node.func.attr in {
                "joinpath",
                "resolve",
                "absolute",
                "with_name",
                "with_suffix",
            }:
                return _store_path(node.func.value, aliases)
        if isinstance(node.func, ast.Name) and node.func.id == "Path" and node.args:
            return _store_path(node.args[0], aliases) or (
                isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and node.args[0].value.startswith(".canon/")
            )
    return False


def _boundary_hits(source: str, *, inside_canon: bool) -> list[str]:
    tree = ast.parse(source)
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.arg)
            and node.arg in {"store", "backend"}
            and isinstance(node.annotation, ast.Name)
            and node.annotation.id == "Path"
        ):
            aliases.add(node.arg)
    for _ in range(4):
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and _store_path(node.value, aliases):
                aliases.update(
                    target.id for target in node.targets if isinstance(target, ast.Name)
                )
            if (
                isinstance(node, ast.AnnAssign)
                and node.value is not None
                and _store_path(node.value, aliases)
                and isinstance(node.target, ast.Name)
            ):
                aliases.add(node.target.id)
    hits: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("orchestra.canon")
            and any(alias.name == "Store" for alias in node.names)
            and not inside_canon
        ):
            hits.append(f"{node.lineno}: imports Store")
        if (
            inside_canon
            and isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Div)
            and _store_path(node.left, aliases)
        ):
            binding = (
                isinstance(node.right, ast.Constant)
                and isinstance(node.right.value, str)
                and node.right.value.startswith("store-binding")
            ) or (
                isinstance(node.right, ast.Name)
                and node.right.id == "name"
                and "store-binding" in source
            )
            global_location = (
                isinstance(node.right, ast.Attribute)
                and node.right.attr == "name"
                and isinstance(node.left, ast.BinOp)
                and isinstance(node.left.right, ast.Constant)
                and node.left.right.value == ".canon"
            )
            if (
                not binding
                and not global_location
                and not (
                    isinstance(node.right, ast.Constant)
                    and node.right.value == ".canon"
                )
            ):
                hits.append(f"{node.lineno}: builds path under store root")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                inside_canon
                and node.func.attr in PATH_METHODS
                and _storage_receiver(node.func.value)
            ):
                hits.append(f"{node.lineno}: calls file-layout method {node.func.attr}")
            if (
                not inside_canon
                and node.func.attr in IO_METHODS
                and _store_path(node.func.value, aliases)
            ):
                hits.append(f"{node.lineno}: performs store file IO ({node.func.attr})")
            if (
                not inside_canon
                and node.func.attr in {"scandir", "listdir", "walk"}
                and node.args
                and _store_path(node.args[0], aliases)
            ):
                hits.append(f"{node.lineno}: traverses store files")
        if (
            not inside_canon
            and isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "open"
            and node.args
            and _store_path(node.args[0], aliases)
        ):
            hits.append(f"{node.lineno}: opens store file")
    return hits


def test_canon_callers_do_not_build_file_backend_paths() -> None:
    hits = [
        f"{path.relative_to(ROOT)}:{hit}"
        for path in sorted((ROOT / "orchestra" / "canon").glob("*.py"))
        if path.name not in FILE_BACKEND
        for hit in _boundary_hits(path.read_text(), inside_canon=True)
    ]
    assert not hits, "R5: file layout must stay in file backend:\n" + "\n".join(hits)


def _outside_sources() -> list[Path]:
    return [
        path
        for directory in ("orchestra", "dashboard", "installer", "hosts")
        for path in (ROOT / directory).rglob("*.py")
        if ROOT / "orchestra" / "canon" not in path.parents
        and ROOT / "orchestra" / "sessions" not in path.parents
    ]


def test_external_modules_do_not_import_store() -> None:
    hits = [
        f"{path.relative_to(ROOT)}:{hit}"
        for path in _outside_sources()
        for hit in _boundary_hits(path.read_text(), inside_canon=False)
        if "imports Store" in hit
    ]
    assert not hits, "R10: use Project outside canon:\n" + "\n".join(hits)


def test_external_modules_do_not_open_store_files() -> None:
    hits = [
        f"{path.relative_to(ROOT)}:{hit}"
        for path in _outside_sources()
        for hit in _boundary_hits(path.read_text(), inside_canon=False)
        if "imports Store" not in hit
    ]
    assert not hits, "R11: use Project instead of store file IO:\n" + "\n".join(hits)


@pytest.mark.parametrize(
    ("source", "inside_canon", "expected"),
    [
        (
            'def leak(store_root):\n    return store_root / "schemas" / "alpha.json"\n',
            True,
            "builds path",
        ),
        (
            "from orchestra.canon.store import Store as FileStore\n",
            False,
            "imports Store",
        ),
        (
            'def leak(project):\n    path = project.store_path / "records" / "bad.md"\n    return path.read_text()\n',
            False,
            "store file IO",
        ),
        (
            'def leak(root):\n    path = root / ".canon" / "config.json"\n    return open(path).read()\n',
            False,
            "opens store file",
        ),
        (
            'def leak(target):\n    return os.scandir(target.store_path / "records")\n',
            False,
            "traverses store files",
        ),
    ],
)
def test_boundary_scan_rejects_seeded_violations(
    source: str, inside_canon: bool, expected: str
) -> None:
    assert any(
        expected in hit for hit in _boundary_hits(source, inside_canon=inside_canon)
    )


def test_boundary_scan_allows_project_api_and_unrelated_paths() -> None:
    source = 'from orchestra.canon.project import Project\ndef read(project: Project, root):\n    text = (root / "README.md").read_text()\n    return project.records(), text\n'
    assert _boundary_hits(source, inside_canon=False) == []
