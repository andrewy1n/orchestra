from __future__ import annotations

import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CONDUCTOR = Path("orchestra/conductor")
TASK_CLOSE = CONDUCTOR / "task_close.py"
CLOSE_BATCH = CONDUCTOR / "close_batch.py"
LOADER_PREFIXES = ("load_", "list_")
LOADER_SUFFIXES = ("_loader", "_lister")


def r18_violations(root: Path) -> list[str]:
    return []


def r19_violations(root: Path) -> list[str]:
    return []


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


@pytest.mark.parametrize(
    "seed",
    [
        "from pathlib import Path\n\n\ndef decide_close(project, *, cwd: Path) -> None:\n    pass\n",
        "def build_batch(request, project, *, cwd=None):\n    return []\n",
    ],
)
def test_r18_guard_accepts_signatures_without_loaders(tmp_path: Path, seed: str) -> None:
    target = tmp_path / TASK_CLOSE
    target.parent.mkdir(parents=True)
    target.write_text(seed, encoding="utf-8")
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
