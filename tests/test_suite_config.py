from __future__ import annotations

import json
from pathlib import Path

from orchestra.conductor.suite import load_suite_policy


def _write_config(root: Path, *, mode: str, command: str, gate: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "orchestra.toml").write_text(
        '[verify.stages]\nphase = ["unit"]\n\n'
        '[verify.unit]\nrunner = ["python3", "-m", "pytest", "{tests}", "--junitxml={report}"]\n\n'
        f"[suite]\nmode = {json.dumps(mode)}\n"
        f"command = {json.dumps(command)}\n"
        f"gate = {json.dumps(gate)}\n",
        encoding="utf-8",
    )


def test_toml_policy_controls_phase_suite(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        mode="full",
        command="pytest tests -q",
        gate="advisory",
    )

    policy = load_suite_policy(tmp_path)

    assert (policy.mode, policy.command, policy.gate) == (
        "full",
        "pytest tests -q",
        "advisory",
    )
    assert policy.source_path == str(tmp_path / "orchestra.toml")


def test_suite_loader_ignores_canon_policy(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        mode="smoke",
        command="pytest -k from_toml",
        gate="required",
    )
    canon = tmp_path / ".canon"
    canon.mkdir()
    (canon / "config.json").write_text(
        json.dumps(
            {
                "settings": {
                    "conductor": {
                        "phase_gate": {
                            "suite": {
                                "mode": "full",
                                "command": "pytest -k from_canon",
                                "gate": "advisory",
                            }
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    policy = load_suite_policy(tmp_path)

    assert (policy.mode, policy.command, policy.gate) == (
        "smoke",
        "pytest -k from_toml",
        "required",
    )


def test_repository_canon_config_contains_only_store_mechanics() -> None:
    config_path = Path(__file__).resolve().parents[1] / ".canon" / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert config["backend"] == "sqlite"
    assert config["schemas"]
    assert "settings" not in config
