from __future__ import annotations

from pathlib import Path

from tests.test_boundaries import _imports

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


def package_order_violations(package: Path) -> list[str]:
    violations = []
    for path in sorted(package.rglob("*.py")):
        rel = path.relative_to(package.parent)
        owner = _package(rel.with_suffix("").parts)
        if owner is None:
            continue
        for lineno, module in _imports(path):
            target = _package(tuple(module.split(".")))
            if target is None or target == owner:
                continue
            if (owner, target) in CYCLE_ALLOWED:
                continue
            if RANKS[target] >= RANKS[owner]:
                violations.append(f"{rel}:{lineno}: {owner} imports {module}")
    return violations
