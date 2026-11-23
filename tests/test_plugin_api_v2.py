from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import orchestra.canon.extensions as extensions

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "third-party-plugins"


def _plugin(api_version: str) -> SimpleNamespace:
    metadata_entries = (
        SimpleNamespace(name="version", value=api_version, group=extensions.PLUGIN_API_GROUP),
        SimpleNamespace(name="demo", value="{}", group=extensions.PLUGIN_CONFIG_GROUP),
    )
    return SimpleNamespace(
        name="demo",
        value="demo:Plugin",
        dist=SimpleNamespace(
            metadata={"Name": "demo-dist"}, version="1.0.0", entry_points=metadata_entries
        ),
        load=lambda: "loaded",
    )


def _install(monkeypatch: pytest.MonkeyPatch, plugin: SimpleNamespace) -> None:
    def discover(*, group: str) -> tuple[SimpleNamespace, ...]:
        return (plugin,) if group == "orchestra.tuner.verify" else ()

    monkeypatch.setattr(extensions.metadata, "entry_points", discover)


def _failed_imports(statements: list[str]) -> list[str]:
    failures: list[str] = []
    for statement in statements:
        try:
            exec(statement, {})
        except Exception as exc:
            failures.append(f"{statement}: {type(exc).__name__}: {exc}")
    return failures


def _orchestra_imports(source: str) -> list[str]:
    statements: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if (isinstance(node, ast.ImportFrom) and (node.module or "").startswith("orchestra")) or (
            isinstance(node, ast.Import)
            and any(alias.name.startswith("orchestra") for alias in node.names)
        ):
            statements.append(ast.unparse(node))
    return statements


def test_plugin_api_version_is_two() -> None:
    assert extensions.PLUGIN_API_VERSION == "2"


def test_registry_rejects_version_one_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, _plugin("1"))

    with pytest.raises(extensions.PluginCatalogError, match="unsupported API version '1'"):
        extensions.resolve_plugin("tuner.verify", "demo")


def test_registry_loads_version_two_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, _plugin("2"))

    registration = extensions.resolve_plugin("tuner.verify", "demo")

    assert registration.descriptor.api_version == "2"
    assert registration.load() == "loaded"


def test_docs_python_imports_resolve() -> None:
    text = (ROOT / "docs" / "plugins.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```python\n(.*?)```", text, flags=re.DOTALL)
    statements = [stmt for block in blocks for stmt in _orchestra_imports(block)]

    assert statements
    assert _failed_imports(statements) == []


def test_docs_declare_version_two_entry() -> None:
    text = (ROOT / "docs" / "plugins.md").read_text(encoding="utf-8")

    assert re.search(r"^v2 = ", text, flags=re.MULTILINE)
    assert not re.search(r"^v1 = ", text, flags=re.MULTILINE)


def test_example_plugin_imports_resolve() -> None:
    statements = [
        stmt
        for path in sorted((EXAMPLE / "src").rglob("*.py"))
        for stmt in _orchestra_imports(path.read_text(encoding="utf-8"))
    ]

    assert statements
    assert _failed_imports(statements) == []


def test_example_declares_version_two_entry() -> None:
    project = tomllib.loads((EXAMPLE / "pyproject.toml").read_text(encoding="utf-8"))

    assert set(project["project"]["entry-points"]["orchestra.plugin_api"]) == {"v2"}


def test_package_declares_version_two_entry() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert set(project["project"]["entry-points"]["orchestra.plugin_api"]) == {"v2"}
