from __future__ import annotations

import ast
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CONDUCTOR = Path("orchestra/conductor")
TASK_CLOSE = CONDUCTOR / "task_close.py"
CLOSE_BATCH = CONDUCTOR / "close_batch.py"
LOADER_PREFIXES = ("load_", "list_")
LOADER_SUFFIXES = ("_loader", "_lister")


def _is_loader_parameter(arg: ast.arg) -> bool:
    if arg.arg.startswith(LOADER_PREFIXES) or arg.arg.endswith(LOADER_SUFFIXES):
        return True
    if arg.annotation is None:
        return False
    return any(
        (isinstance(node, ast.Name) and node.id == "Callable")
        or (isinstance(node, ast.Attribute) and node.attr == "Callable")
        or (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and "Callable" in node.value
        )
        for node in ast.walk(arg.annotation)
    )


def _parameters(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.arg]:
    args = node.args
    found = [*args.posonlyargs, *args.args, *args.kwonlyargs]
    found.extend(arg for arg in (args.vararg, args.kwarg) if arg is not None)
    return found


def _is_gate_function(path: Path, name: str) -> bool:
    if path == CLOSE_BATCH:
        return name == "build_batch"
    return name == "decide_close" or "enforce" in name or name.endswith("_gate") or "_gate_" in name


def r18_violations(root: Path) -> list[str]:
    found: list[str] = []
    for relative in (TASK_CLOSE, CLOSE_BATCH):
        tree = ast.parse((root / relative).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_gate_function(
                relative, node.name
            ):
                found.extend(
                    f"{relative}:{arg.lineno}:{node.name}({arg.arg})"
                    for arg in _parameters(node)
                    if _is_loader_parameter(arg)
                )
    return found


def _is_cwd_call(node: ast.expr) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr in {"cwd", "getcwd"}:
        return True
    if isinstance(func, ast.Name) and func.id == "Path" and len(node.args) == 1:
        return _is_cwd_call(node.args[0])
    return False


def _callee(node: ast.Call) -> str:
    func = node.func
    return func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")


def _root_argument(node: ast.Call, keyword: str) -> ast.expr | None:
    if node.args:
        return node.args[0]
    return next((kw.value for kw in node.keywords if kw.arg == keyword), None)


def _opens_store_from_cwd(node: ast.Call) -> bool:
    name = _callee(node)
    if name == "open_store":
        root = _root_argument(node, "directory")
    elif name == "resolve_location":
        root = _root_argument(node, "store")
    else:
        return False
    return root is not None and any(
        isinstance(part, ast.Call) and _is_cwd_call(part) for part in ast.walk(root)
    )


def r19_violations(root: Path) -> list[str]:
    found: list[str] = []
    for path in sorted((root / CONDUCTOR).rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        found.extend(
            f"{path.relative_to(root)}:{node.lineno}"
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and _opens_store_from_cwd(node)
        )
    return found


def _copy_conductor(tmp_path: Path) -> Path:
    shutil.copytree(
        REPO / CONDUCTOR, tmp_path / CONDUCTOR, ignore=shutil.ignore_patterns("__pycache__")
    )
    return tmp_path


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_r18_guard_passes_on_tree() -> None:
    assert r18_violations(REPO) == []


def test_r18_guard_fails_on_callable_parameter_in_build_batch(tmp_path: Path) -> None:
    root = _copy_conductor(tmp_path)
    _replace(
        root / CLOSE_BATCH,
        "    project: Project,\n    *,\n    cwd: str | Path | None = None,\n) -> list[JsonObject]:",
        "    project: Project,\n    *,\n    fetch: Callable[[str], object],\n    cwd: str | Path | None = None,\n) -> list[JsonObject]:",
    )
    assert len(r18_violations(root)) == 1


def test_r18_guard_fails_on_load_named_parameter_in_decide_close(tmp_path: Path) -> None:
    root = _copy_conductor(tmp_path)
    _replace(
        root / TASK_CLOSE,
        "def decide_close(\n    project: Project,\n",
        "def decide_close(\n    project: Project,\n    load_acceptance,\n",
    )
    assert len(r18_violations(root)) == 1


def test_r18_guard_fails_on_callable_parameter_in_a_gate(tmp_path: Path) -> None:
    root = _copy_conductor(tmp_path)
    _replace(
        root / TASK_CLOSE,
        "def _enforce_close_gates(\n    project: Project,\n",
        "def _enforce_close_gates(\n    project: Project,\n    lister: Callable[[], list[object]],\n",
    )
    assert len(r18_violations(root)) == 1


def test_r18_guard_accepts_signatures_without_loaders(tmp_path: Path) -> None:
    (tmp_path / CONDUCTOR).mkdir(parents=True)
    (tmp_path / TASK_CLOSE).write_text(
        "from pathlib import Path\n\n\n"
        "def decide_close(project, *, cwd: Path) -> None:\n    pass\n",
        encoding="utf-8",
    )
    (tmp_path / CLOSE_BATCH).write_text(
        "def build_batch(request, project, *, cwd=None):\n    return []\n", encoding="utf-8"
    )
    assert r18_violations(tmp_path) == []


def test_r19_guard_passes_on_tree() -> None:
    assert r19_violations(REPO) == []


@pytest.mark.parametrize(
    "seed",
    [
        "from pathlib import Path\n\nfrom orchestra.canon.project import open_store\n\n\n"
        "def run():\n    return open_store(Path.cwd())\n",
        "import os\n\nfrom orchestra.canon.project import open_store\n\n\n"
        "def run():\n    return open_store(os.getcwd(), store=None)\n",
        "from pathlib import Path\n\nfrom orchestra.canon.project import open_store\n\n\n"
        "def run():\n    return open_store(directory=Path.cwd())\n",
        "from pathlib import Path\n\nfrom orchestra.store import resolve_location\n\n\n"
        "def run():\n    return resolve_location(Path.cwd(), Path('x')).open()\n",
        "from pathlib import Path\n\nfrom orchestra.canon.project import open_store\n\n\n"
        "def run(root=None):\n    return open_store(root or Path.cwd())\n",
        "from pathlib import Path\n\nfrom orchestra.canon.project import open_store\n\n\n"
        "def run(root=None):\n    return open_store(root if root else Path.cwd(), store=None)\n",
    ],
)
def test_r19_guard_fails_on_seeded_cwd_store_open(tmp_path: Path, seed: str) -> None:
    root = _copy_conductor(tmp_path)
    (root / CONDUCTOR / "seeded_cwd_open.py").write_text(seed, encoding="utf-8")
    found = r19_violations(root)
    assert len(found) == 1
    assert found[0].startswith("orchestra/conductor/seeded_cwd_open.py:")


def test_r19_guard_accepts_cwd_as_resolve_location_fallback(tmp_path: Path) -> None:
    root = _copy_conductor(tmp_path)
    (root / CONDUCTOR / "seeded_fallback.py").write_text(
        "from pathlib import Path\n\nfrom orchestra.store import resolve_location\n\n\n"
        "def run(store):\n    return resolve_location(store, Path.cwd()).open()\n",
        encoding="utf-8",
    )
    assert r19_violations(root) == []
