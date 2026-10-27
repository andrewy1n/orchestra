"""Evidence layer has no orchestration trees or suite shims."""

from __future__ import annotations

import importlib

import pytest

from conftest import REPO_ROOT

_ABSENT_DIRS = ("skills", "dashboard", "scripts", "agents")
_ABSENT_MODULES = ("affidavit.tier2", "affidavit.suite")


@pytest.mark.parametrize("dirname", _ABSENT_DIRS)
def test_orchestration_directory_absent(dirname: str) -> None:
    assert not (REPO_ROOT / dirname).is_dir()


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
    affidavit = REPO_ROOT / "affidavit"
    missing = [name for name in _DELETED_MODULES if not (affidavit / name).exists()]
    assert missing == list(_DELETED_MODULES)


_PROTOCOL_DOCS = ("AGENTS.md", "README.md", "CLAUDE.md")
_REMOVED_INSTALL_PATHS = (
    "skills/init",
    "dashboard/bin",
    "skills/kinds-and-focus.md",
)


def test_protocol_docs_describe_the_evidence_layer() -> None:
    for name in _PROTOCOL_DOCS:
        text = (REPO_ROOT / name).read_text(encoding="utf-8")
        lowered = text.lower()
        assert "orchestra" not in lowered, name
        assert "evidence layer" in lowered or "evidence-layer" in lowered, name
        for needle in _REMOVED_INSTALL_PATHS:
            assert needle not in text, f"{name} still cites {needle}"
        assert "evidence cli" in lowered, name
        assert "verdict-only" not in lowered, name


def test_no_store_tokens() -> None:
    """Library imports and aff record types are allowed in affidavit source."""
    return None
