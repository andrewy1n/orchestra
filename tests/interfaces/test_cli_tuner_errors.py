"""Tuner verbs export kit commands and write prefixed error lines."""

from __future__ import annotations

from pathlib import Path

import pytest

from interfaces.interfaces_support import invoke
from orchestra.tuner import cli as tuner_cli

BIND = ("bind", "--observation", "o", "--claim", "X", "--base", "a", "--head", "b")


def test_tuner_cli_exports_verify_passthrough_and_plugins() -> None:
    commands = {command.name: command for command in tuner_cli.commands()}

    assert set(commands) == {"verify", "plugins"}
    assert commands["verify"].passthrough is True
    assert commands["plugins"].passthrough is False


@pytest.mark.parametrize(
    ("argv", "prefix", "code"),
    [
        pytest.param(
            ("verify", "verdict", "--at", "HEAD", "c"),
            "orchestra verify verdict:",
            2,
            id="verdict_manifest",
        ),
        pytest.param(
            ("verify", "assertion-red", "missing.json"),
            "orchestra verify assertion-red:",
            2,
            id="assertion_red_unreadable",
        ),
        pytest.param(("verify", "trail"), "orchestra verify trail:", 2, id="trail_no_store"),
        pytest.param(("verify", *BIND), "orchestra verify bind:", 2, id="bind_no_store"),
        pytest.param(
            ("verify", "unbind", "--id", "x"), "orchestra verify unbind:", 2, id="unbind_no_store"
        ),
        pytest.param(
            ("verify", "recheck", "--claim", "X"),
            "orchestra verify recheck:",
            2,
            id="recheck_no_store",
        ),
        pytest.param(
            ("verify", "plugins", "--stage", "task", "--key", "missing-key"),
            "orchestra verify plugins:",
            2,
            id="verify_plugins_failure",
        ),
    ],
)
def test_tuner_error_line_starts_with_the_command_path(
    argv: tuple[str, ...], prefix: str, code: int, bare_dir: Path
) -> None:
    result = invoke("orchestra", list(argv), bare_dir)

    assert result.code == code
    lines = [line for line in result.err.splitlines() if line]
    assert lines
    assert lines[-1].startswith(prefix), result.err


def test_verify_passes_an_unknown_claim_argument_to_the_tuner(bare_dir: Path) -> None:
    result = invoke("orchestra", ["verify", "verdict", "--at", "HEAD", "no-such-claim"], bare_dir)

    assert result.code == 2
    assert "unrecognized arguments" not in result.err
    assert result.err.splitlines()[-1].startswith("orchestra verify verdict:"), result.err


def test_non_passthrough_verb_rejects_an_unknown_flag(bare_dir: Path) -> None:
    result = invoke("orchestra", ["gate", "x", "--bogus"], bare_dir)

    assert result.code == 2
    assert "unrecognized arguments" in result.err
