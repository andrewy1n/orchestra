"""A Landing `suite:` line replaces the configured suite command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestra import cli as orchestra_cli
from orchestra.conductor import suite

PHASE = "landing-suite-phase"
EFFORT = "landing-suite-effort"
CONFIG_COMMAND = "true # config"
LANDING_COMMAND = "uv run pytest -q tests/fast"
BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n"


def _seed(store: Path, cli, landing_lines: tuple[str, ...]) -> None:
    config_path = store / ".canon" / "config.json"
    config = json.loads(config_path.read_text())
    config.setdefault("settings", {})["conductor"] = {
        "phase_gate": {"suite": {"mode": "smoke", "command": CONFIG_COMMAND, "gate": "advisory"}}
    }
    config_path.write_text(json.dumps(config))
    body = BODY
    if landing_lines:
        body += "\n## Landing\n\n" + "\n".join(landing_lines) + "\n"
    for record_type, subject, payload, text in (
        ("score:effort", EFFORT, {"goal": "g", "kind": "deliver"}, None),
        (
            "score:phase",
            PHASE,
            {"title": PHASE, "ordinal": 1, "effort": EFFORT},
            body,
        ),
    ):
        args = [
            "create",
            "--type",
            record_type,
            "--subject",
            subject,
            "--payload",
            json.dumps(payload),
        ]
        if text is not None:
            args.extend(["--body", text])
        result = cli(*args)
        assert result.returncode == 0, result.stdout + result.stderr


def _policy(store: Path, capsys: pytest.CaptureFixture[str]) -> dict[str, object]:
    code = orchestra_cli.main(
        ["suite", "policy", "--phase", PHASE, "--cwd", str(store), "--store", str(store)]
    )
    assert code == 0
    return json.loads(capsys.readouterr().out)


def _started_policy(
    store: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> suite.SuitePolicy:
    seen: list[suite.SuitePolicy] = []

    def fake_start(**kwargs: object) -> suite.SuiteStart:
        policy = kwargs["policy"]
        assert isinstance(policy, suite.SuitePolicy)
        seen.append(policy)
        return suite.SuiteStart(
            session_name="s",
            worktree=store,
            phase_slug=PHASE,
            phase_head="h",
            log_path=store / "log",
            exit_path=store / "exit",
            started_monotonic=0.0,
            policy=policy,
        )

    monkeypatch.setattr(suite, "start_suite_background", fake_start)
    code = orchestra_cli.main(
        ["suite", "start", "--phase", PHASE, "--cwd", str(store), "--store", str(store)]
    )
    capsys.readouterr()
    assert code == 0
    assert len(seen) == 1
    return seen[0]


def test_landing_suite_line_overrides_config_command(
    store: Path, cli, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _seed(store, cli, ("- merge: `true`", f"- suite: `{LANDING_COMMAND}`"))
    document = _policy(store, capsys)
    assert document["command"] == LANDING_COMMAND
    assert document["mode"] == "smoke"
    assert document["gate"] == "advisory"
    started = _started_policy(store, monkeypatch, capsys)
    assert started.command == LANDING_COMMAND
    assert started.mode == "smoke"
    assert started.gate == "advisory"


def test_no_landing_suite_uses_config(
    store: Path, cli, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _seed(store, cli, ("- merge: `true`",))
    assert _policy(store, capsys)["command"] == CONFIG_COMMAND
    assert _started_policy(store, monkeypatch, capsys).command == CONFIG_COMMAND
