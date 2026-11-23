from __future__ import annotations

import ast
from pathlib import Path

CONDUCTOR_ORDER: tuple[frozenset[str], ...] = (
    frozenset({"verification/evidence"}),
    frozenset({"verification"}),
    frozenset({"verification/suite", "verification/review"}),
    frozenset({"landing"}),
    frozenset({"tasks"}),
    frozenset({"tasks/close", "tasks/redispatch"}),
    frozenset({"phases/progress"}),
    frozenset({"phases/workflow"}),
)
CYCLE_ALLOWED = frozenset({("tasks", "tasks/close"), ("tasks/close", "tasks")})
CONDUCTOR_ROOT = ("orchestra", "conductor")
RELATIVE = "."
RANKS = {name: rank for rank, names in enumerate(CONDUCTOR_ORDER) for name in names}


def _package(parts: tuple[str, ...]) -> str | None:
    if parts[:2] != CONDUCTOR_ROOT:
        return None
    inner = parts[2:]
    for size in range(len(inner), 0, -1):
        name = "/".join(inner[:size])
        if name in RANKS:
            return name
    return None


def _dotted_imports(path: Path) -> list[tuple[int, str]]:
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))):
        if isinstance(node, ast.ImportFrom):
            if node.level:
                found.append((node.lineno, RELATIVE))
            elif node.module:
                found.extend((node.lineno, f"{node.module}.{alias.name}") for alias in node.names)
        elif isinstance(node, ast.Import):
            found.extend((node.lineno, alias.name) for alias in node.names)
    return found


def package_order_violations(package: Path) -> list[str]:
    violations = set()
    for path in sorted(package.rglob("*.py")):
        rel = path.relative_to(package.parent)
        if rel.parts[:2] != CONDUCTOR_ROOT:
            continue
        owner = _package(rel.with_suffix("").parts)
        for lineno, dotted in _dotted_imports(path):
            if dotted == RELATIVE:
                violations.add(f"{rel}:{lineno}: relative import")
                continue
            target = _package(tuple(dotted.split(".")))
            if owner is None or target is None or target == owner:
                continue
            if (owner, target) in CYCLE_ALLOWED or RANKS[target] < RANKS[owner]:
                continue
            module = ".".join((*CONDUCTOR_ROOT, *target.split("/")))
            violations.add(f"{rel}:{lineno}: {owner} imports {module}")
    return sorted(violations)
