"""Orchestra owns reviewer and suite; tier2 stays deleted."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_reviewer_and_suite_import():
    import orchestra.conductor.reviewer  # noqa: F401
    import orchestra.conductor.suite  # noqa: F401


def test_tier2_module_raises_import_error():
    with pytest.raises(ImportError):
        import orchestra.tier2  # noqa: F401


def test_tuner_tier2_file_absent():
    root = Path(__file__).resolve().parents[1]
    assert not (root / "tuner" / "tier2.py").is_file()
