from __future__ import annotations

import ast
from pathlib import Path

import pytest

from orchestra import plugin_evidence, plugins
from orchestra.conductor.review_technique import ReviewTechnique
from orchestra.tuner import plugin_evidence as tuner_evidence
from orchestra.tuner import plugins as tuner_plugins
from orchestra.tuner.technique import TechniqueResult, validate_technique_result


def test_evidence_dispatch_is_owned_by_tuner() -> None:
    assert plugins.dispatch_plugins is tuner_plugins.dispatch_plugins
    assert plugins.dispatch_plugins.__module__ == "orchestra.tuner.plugins"
    assert plugin_evidence.dispatch_signed_plugins is tuner_evidence.dispatch_signed_plugins
    assert tuner_evidence.dispatch_signed_plugins.__module__ == "orchestra.tuner.plugin_evidence"


def test_evidence_verification_is_owned_by_tuner() -> None:
    assert plugin_evidence.verify_plugin_evidence is tuner_evidence.verify_plugin_evidence
    assert tuner_evidence.verify_plugin_evidence.__module__ == "orchestra.tuner.plugin_evidence"


def test_review_technique_owns_validation_and_tuner_has_no_conductor_imports() -> None:
    output = (
        "verdict: PASS\nfindings: []\nintegration:\n"
        "  interfaces: stable\n  assumptions: reviewed\n"
        "  invariants: preserved\n  conflicts: none\n"
    )
    result = TechniqueResult("pass", {"verdict": "PASS", "reviewer_output": output})

    assert validate_technique_result(ReviewTechnique(), result) == result
    with pytest.raises(ValueError):
        validate_technique_result(
            ReviewTechnique(), TechniqueResult("pass", {"verdict": "PASS", "reviewer_output": ""})
        )

    source_root = Path(tuner_plugins.__file__).parent
    tuner_files = (source_root / "plugins.py", source_root / "plugin_evidence.py")
    for path in tuner_files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        imported.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        assert not any(name and name.startswith("orchestra.conductor") for name in imported)

    package_config = Path(__file__).resolve().parents[1] / "pyproject.toml"
    text = package_config.read_text(encoding="utf-8")
    assert 'review = "orchestra.conductor.review_technique:ReviewTechnique"' in text
    assert 'unit = "orchestra.tuner.plugins:UnitPlugin"' in text
