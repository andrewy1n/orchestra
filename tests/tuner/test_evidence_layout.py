"""Evidence layer has no orchestration trees or suite shims."""

from __future__ import annotations

import importlib

import pytest

from conftest import REPO_ROOT

_ABSENT_DIRS = ("skills", "dashboard", "scripts", "agents")
_ABSENT_MODULES = ("orchestra.tuner.tier2", "orchestra.tuner.suite")


@pytest.mark.parametrize("dirname", _ABSENT_DIRS)
def test_orchestration_directory_absent(dirname: str) -> None:
    assert not (REPO_ROOT / "orchestra" / "tuner" / dirname).is_dir()


@pytest.mark.parametrize("module", _ABSENT_MODULES)
def test_moved_module_does_not_import(module: str) -> None:
    with pytest.raises(ImportError):
        importlib.import_module(module)


_DELETED_MODULES = (
    "aa.py",
    "aa_resolve.py",
    "check.py",
    "close_batch.py",
    "policy.py",
)


def test_store_modules_absent() -> None:
    tuner = REPO_ROOT / "orchestra" / "tuner"
    missing = [name for name in _DELETED_MODULES if not (tuner / name).exists()]
    assert missing == list(_DELETED_MODULES)
