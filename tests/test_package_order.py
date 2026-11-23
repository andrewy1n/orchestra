from __future__ import annotations

from pathlib import Path

from tests.package_order_support import CONDUCTOR_ORDER, package_order_violations
from tests.test_boundaries import PACKAGE


def _write(root: Path, rel: str, source: str) -> None:
    path = root / "orchestra" / "conductor" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def test_conductor_packages_import_only_lower_packages():
    assert package_order_violations(PACKAGE) == []


def test_order_table_lists_the_agreed_packages():
    assert [sorted(rank) for rank in CONDUCTOR_ORDER] == [
        ["verification/evidence"],
        ["verification"],
        ["verification/review", "verification/suite"],
        ["landing"],
        ["tasks"],
        ["tasks/close", "tasks/redispatch"],
        ["phases/progress"],
        ["phases/workflow"],
    ]


def test_scan_rejects_an_upward_import(tmp_path: Path):
    _write(tmp_path, "verification/evidence/__init__.py", "")
    _write(
        tmp_path, "verification/evidence/leak.py", "from orchestra.conductor.landing import land\n"
    )
    _write(tmp_path, "landing/__init__.py", "")
    assert package_order_violations(tmp_path / "orchestra") == [
        "orchestra/conductor/verification/evidence/leak.py:1: "
        "verification/evidence imports orchestra.conductor.landing"
    ]


def test_scan_accepts_a_downward_import(tmp_path: Path):
    _write(tmp_path, "landing/use.py", "from orchestra.conductor.verification.evidence import x\n")
    assert package_order_violations(tmp_path / "orchestra") == []


def test_scan_accepts_a_same_rank_sibling_import_only_within_the_package(tmp_path: Path):
    _write(
        tmp_path,
        "verification/suite/a.py",
        "from orchestra.conductor.verification.review import x\n",
    )
    assert package_order_violations(tmp_path / "orchestra") == [
        "orchestra/conductor/verification/suite/a.py:1: "
        "verification/suite imports orchestra.conductor.verification.review"
    ]


def test_leaf_modules_are_importable_from_every_package(tmp_path: Path):
    _write(tmp_path, "verification/evidence/a.py", "from orchestra.conductor import model_types\n")
    _write(tmp_path, "phases/workflow/b.py", "from orchestra.conductor.workspace_types import W\n")
    assert package_order_violations(tmp_path / "orchestra") == []


def test_tasks_and_tasks_close_may_import_each_other(tmp_path: Path):
    _write(tmp_path, "tasks/a.py", "from orchestra.conductor.tasks.close import x\n")
    _write(tmp_path, "tasks/close/b.py", "from orchestra.conductor.tasks import y\n")
    assert package_order_violations(tmp_path / "orchestra") == []


def test_tasks_close_may_not_import_redispatch(tmp_path: Path):
    _write(tmp_path, "tasks/close/b.py", "from orchestra.conductor.tasks.redispatch import y\n")
    assert package_order_violations(tmp_path / "orchestra") == [
        "orchestra/conductor/tasks/close/b.py:1: "
        "tasks/close imports orchestra.conductor.tasks.redispatch"
    ]
