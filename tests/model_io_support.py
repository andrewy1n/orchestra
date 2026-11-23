from __future__ import annotations

import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "orchestra"
COMPONENTS = ("score", "composer", "tuner", "conductor")
OPERATION = "operation"
IO_MODULES = {
    "fcntl",
    "glob",
    "io",
    "shutil",
    "socket",
    "sqlite3",
    "subprocess",
    "tempfile",
    "urllib",
}
OS_FILE_CALLS = {
    "chmod",
    "fsync",
    "listdir",
    "makedirs",
    "mkdir",
    "open",
    "remove",
    "removedirs",
    "rename",
    "rmdir",
    "scandir",
    "stat",
    "symlink",
    "unlink",
    "utime",
    "walk",
}
OS_PATH_CALLS = {
    "exists",
    "getatime",
    "getctime",
    "getmtime",
    "getsize",
    "isdir",
    "isfile",
    "islink",
    "ismount",
    "lexists",
    "realpath",
    "samefile",
    "sameopenfile",
    "samestat",
}
PATH_METHODS = {
    "cwd",
    "exists",
    "glob",
    "home",
    "is_dir",
    "is_file",
    "iterdir",
    "mkdir",
    "open",
    "read_bytes",
    "read_text",
    "resolve",
    "rglob",
    "rmdir",
    "samefile",
    "stat",
    "touch",
    "unlink",
    "write_bytes",
    "write_text",
}


def undeclared_packages(root: Path, declarations: dict[str, str]) -> list[str]:
    found = set()
    for component in COMPONENTS:
        for path in (root / component).rglob("*.py"):
            if "__pycache__" not in path.parts:
                found.add(path.parent.relative_to(root).as_posix())
    return sorted(found - declarations.keys())


def _violations(tree: ast.AST) -> list[tuple[int, str]]:
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(
                (node.lineno, f"imports {alias.name}")
                for alias in node.names
                if alias.name.split(".")[0] in IO_MODULES
            )
        elif isinstance(node, ast.ImportFrom):
            if node.level or not node.module:
                continue
            if node.module.split(".")[0] in IO_MODULES:
                found.append((node.lineno, f"imports {node.module}"))
            elif node.module == "os":
                found.extend(
                    (node.lineno, f"imports os.{alias.name}")
                    for alias in node.names
                    if alias.name in OS_FILE_CALLS
                )
            elif node.module == "os.path":
                found.extend(
                    (node.lineno, f"imports os.path.{alias.name}")
                    for alias in node.names
                    if alias.name in OS_PATH_CALLS
                )
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "open":
                found.append((node.lineno, "calls open()"))
            elif isinstance(func, ast.Attribute):
                owner = func.value
                if isinstance(owner, ast.Name) and owner.id == "os" and func.attr in OS_FILE_CALLS:
                    found.append((node.lineno, f"calls os.{func.attr}()"))
                elif (
                    isinstance(owner, ast.Attribute)
                    and owner.attr == "path"
                    and isinstance(owner.value, ast.Name)
                    and owner.value.id == "os"
                    and func.attr in OS_PATH_CALLS
                ):
                    found.append((node.lineno, f"calls os.path.{func.attr}()"))
                elif func.attr == "resolve" and node.args:
                    continue
                elif func.attr in PATH_METHODS:
                    found.append((node.lineno, f"calls .{func.attr}()"))
    return sorted(found)


def io_violations(root: Path, declarations: dict[str, str]) -> list[str]:
    found = []
    for path in sorted(root.rglob("*.py")):
        package = path.parent.relative_to(root).as_posix()
        rel = path.relative_to(root).as_posix()
        kind = declarations.get(rel, declarations.get(package))
        if kind is None or kind == OPERATION:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        found.extend(f"{rel}:{line}: {what}" for line, what in _violations(tree))
    return found
