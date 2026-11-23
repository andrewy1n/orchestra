from __future__ import annotations

import ast
import json
from collections import defaultdict
from pathlib import Path

COMPONENTS = ("score", "composer", "conductor", "tuner")


def owner_map(package: Path) -> dict[str, set[str]]:
    owners: dict[str, set[str]] = defaultdict(set)
    for component in COMPONENTS:
        schema = json.loads((package / component / "schemas" / f"{component}.json").read_text())
        for record_type in schema["types"].values():
            for field in record_type.get("fields", {}):
                owners[field].add(component)
    return owners


def _receiver_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _literal_keys(tree: ast.AST):
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Subscript)
            and _receiver_name(node.value) == "payload"
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        ):
            yield node.slice.value
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and _receiver_name(node.func.value) == "payload"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            yield node.args[0].value


def foreign_reads(
    source: str, component: str, module: str, owners: dict[str, set[str]]
) -> set[str]:
    found: set[str] = set()
    for key in _literal_keys(ast.parse(source)):
        key_owners = owners.get(key)
        if key_owners and len(key_owners) == 1 and component not in key_owners:
            found.add(f"{module} {key}")
    return found


def scan_package(package: Path, owners: dict[str, set[str]]) -> set[str]:
    found: set[str] = set()
    for component in COMPONENTS:
        for path in sorted((package / component).rglob("*.py")):
            parts = path.relative_to(package.parent).with_suffix("").parts
            if parts[-1] == "__init__":
                parts = parts[:-1]
            found |= foreign_reads(path.read_text(), component, ".".join(parts), owners)
    return found


def load_allowlist(path: Path) -> list[str]:
    return [line for line in path.read_text().splitlines() if line]
