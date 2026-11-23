"""Every store-needing verb exits 2 without a store and names its command path."""

from __future__ import annotations

from pathlib import Path

import pytest

import orchestra.cli as root_cli
from interfaces.interfaces_support import invoke
from interfaces.test_cli_no_store import (
    CONDUCTOR_LAND_CLOSE,
    CONDUCTOR_SUITE_GATE,
    CONDUCTOR_WAVE_TASK,
    CONDUCTOR_WORKFLOW,
    LIGHT_COMPONENTS,
    MINIMAL_CONFIG,
    TUNER_CANON_STAGE,
    VIEWS,
)

CHECK_CODE = 4
STORE_VERB_CODE = 2

CASES = [
    *((argv, STORE_VERB_CODE) for argv in CONDUCTOR_SUITE_GATE),
    *((argv, STORE_VERB_CODE) for argv in CONDUCTOR_WAVE_TASK),
    *((argv, STORE_VERB_CODE) for argv in CONDUCTOR_LAND_CLOSE),
    *((argv, STORE_VERB_CODE) for argv in CONDUCTOR_WORKFLOW),
    *((argv, STORE_VERB_CODE) for argv in VIEWS),
    *LIGHT_COMPONENTS,
    *TUNER_CANON_STAGE,
]
PARAMS = [
    pytest.param(argv, code, id="_".join(argv).replace("-", "_").replace("/", "_"))
    for argv, code in dict.fromkeys(CASES)
]


def _run(argv: tuple[str, ...], bare_dir: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ORCHESTRA_STORE", raising=False)
    (bare_dir / "orchestra.toml").write_text(MINIMAL_CONFIG, encoding="utf-8")
    (bare_dir / "close-request.json").write_text("{}", encoding="utf-8")
    return invoke("orchestra", list(argv), bare_dir)


def _command_path(argv: tuple[str, ...]) -> str:
    namespace, _ = root_cli._build_parser().parse_known_args(list(argv))
    return " ".join(("orchestra", *namespace.command_path))


@pytest.mark.parametrize(("argv", "code"), PARAMS)
def test_store_not_ready_exit(
    argv: tuple[str, ...], code: int, bare_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _run(argv, bare_dir, monkeypatch)
    assert result.code == code, result.out + result.err


@pytest.mark.parametrize(("argv", "code"), PARAMS)
def test_store_not_ready_prefix(
    argv: tuple[str, ...], code: int, bare_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _run(argv, bare_dir, monkeypatch)
    assert f"{_command_path(argv)}:" in result.err, result.err
    assert "store_not_ready:" in result.err, result.err


def test_store_not_ready_check_keeps_exit_4() -> None:
    assert (("check", "--acceptance", "nope"), CHECK_CODE) in TUNER_CANON_STAGE
