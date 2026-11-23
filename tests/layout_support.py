import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_map(packages: dict[str, str]) -> dict[str, list[str]]:
    return {package: modules.split() for package, modules in packages.items()}


def layout_problems(component: str, packages: dict[str, list[str]]) -> list[str]:
    base = ROOT / "orchestra" / component
    problems: list[str] = []
    for package, modules in packages.items():
        package_dir = base.joinpath(*package.split("."))
        parts = package.split(".")
        for depth in range(1, len(parts) + 1):
            init = base.joinpath(*parts[:depth]) / "__init__.py"
            if not init.is_file():
                problems.append(f"missing {init.relative_to(ROOT)}")
        for module in modules:
            new = package_dir / f"{module}.py"
            if not new.is_file():
                problems.append(f"missing {new.relative_to(ROOT)}")
            old = base / f"{module}.py"
            if old.exists():
                problems.append(f"remains {old.relative_to(ROOT)}")
    return problems


SCAN_DIRS = ("orchestra", "tests", "dashboard", "installer", "scripts", "evals", "docs")
SKIPPED_PARTS = {".worktrees", "__pycache__", "node_modules", ".venv"}
GUARD_TEST = "tests/test_layout_guards.py"


def moved_old_paths(maps: dict[str, list[dict[str, list[str]]]]) -> dict[str, list[str]]:
    moved: dict[str, list[str]] = {}
    for component, package_maps in maps.items():
        names = sorted(
            {m for packages in package_maps for modules in packages.values() for m in modules}
        )
        moved[component] = [
            name for name in names if not (ROOT / "orchestra" / component / name).is_dir()
        ]
    return moved


def old_path_leftovers(root: Path, moved: dict[str, list[str]]) -> list[str]:
    found = []
    for component, names in moved.items():
        for name in names:
            old = root / "orchestra" / component / f"{name}.py"
            if old.exists():
                found.append(old.relative_to(root).as_posix())
    return sorted(found)


def _scan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for directory in SCAN_DIRS:
        base = root / directory
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            relative = path.relative_to(root)
            if path.suffix not in {".py", ".md"} or not path.is_file():
                continue
            if SKIPPED_PARTS & set(relative.parts) or relative.parts[:2] == (
                ".claude",
                "worktrees",
            ):
                continue
            if relative.as_posix() == GUARD_TEST:
                continue
            files.append(path)
    return files


def _py_imports(source: str) -> list[tuple[int, str]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.append((node.lineno, node.module))
            found.extend((node.lineno, f"{node.module}.{alias.name}") for alias in node.names)
    return found


_MD_IMPORT = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import\s+(.+)|import\s+([\w.]+))")


def _md_imports(source: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for number, line in enumerate(source.splitlines(), 1):
        match = _MD_IMPORT.match(line)
        if not match:
            continue
        if match.group(3):
            found.append((number, match.group(3)))
        else:
            found.append((number, match.group(1)))
            names = re.findall(
                r"\w+",
                match.group(2).split(" as ")[0]
                if " as " not in match.group(2)
                else re.sub(r"\s+as\s+\w+", "", match.group(2)),
            )
            found.extend((number, f"{match.group(1)}.{n}") for n in names)
    return found


def old_path_imports(root: Path, moved: dict[str, list[str]]) -> list[str]:
    old = {f"orchestra.{component}.{name}" for component, names in moved.items() for name in names}
    hits: list[str] = []
    for path in _scan_files(root):
        source = path.read_text(encoding="utf-8", errors="replace")
        imports = _py_imports(source) if path.suffix == ".py" else _md_imports(source)
        for number, dotted in imports:
            for target in old:
                if dotted == target or dotted.startswith(target + "."):
                    hits.append(f"{path.relative_to(root).as_posix()}:{number}: {target}")
                    break
    return sorted(set(hits))
