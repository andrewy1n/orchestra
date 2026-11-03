from pathlib import Path

import pytest

from orchestra.conductor.suite import load_suite_policy


def test_suite_policy_reads_project_config(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "orchestra.toml").write_text(
        '[verify.stages]\nphase = ["unit"]\n\n'
        '[verify.unit]\nrunner = ["python3", "-m", "pytest", "{tests}", "--junitxml={report}"]\n\n'
        '[suite]\nmode = "full"\ncommand = "pytest -q"\ngate = "advisory"\n'
    )
    policy = load_suite_policy(root)
    assert (policy.mode, policy.command, policy.gate) == ("full", "pytest -q", "advisory")
    assert policy.source_path == str(root / "orchestra.toml")


def test_missing_project_config_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="required project config is missing"):
        load_suite_policy(tmp_path)
