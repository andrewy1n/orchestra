"""Failing oracles for `orchestra spawn parse` and `orchestra spawn message`.

Evidence replies are `key: value` lines. Parse returns those lines for the
required keys subject, kind, result, revision, and evidence, keeps an
optional known line, and rejects a missing required line, a result outside
pass/fail/blocked/abandoned, or a key outside the known set. `spawn message`
prints the correction text unchanged.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from conftest import REPO_ROOT

_REQUIRED = (
    ("subject", "build-widget"),
    ("kind", "deliver"),
    ("result", "pass"),
    ("revision", "abc123def"),
    ("evidence", "ran pytest"),
)
_OPTIONAL = (
    ("observations", "saw a red bar"),
    ("root_cause", "off-by-one"),
    ("verdict", "pass"),
    ("metrics", "baseline 1 candidate 2"),
    ("claim", "the gate holds"),
    ("needs_human", "false"),
    ("attempted_action", "none"),
    ("retry_when", "tomorrow"),
    ("blocker", "none"),
)


def _env() -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"CANON_STORE", "ORCHESTRA_STORE"}
    }
    prior = env.get("PYTHONPATH", "")
    parts = [str(REPO_ROOT)]
    if prior:
        parts.append(prior)
    env["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(parts))
    return env


def _run(args: list[str], *, stdin: str) -> subprocess.CompletedProcess[str]:
    work = Path(tempfile.mkdtemp(prefix="spawn-oracle-"))
    try:
        return subprocess.run(
            [sys.executable, "-m", "orchestra.cli", *args],
            input=stdin,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=str(work),
            env=_env(),
            check=False,
        )
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _lines(lines: tuple[tuple[str, str], ...] | list[tuple[str, str]]) -> str:
    return "".join(f"{key}: {value}\n" for key, value in lines)


def _parse(text: str) -> subprocess.CompletedProcess[str]:
    return _run(["spawn", "parse"], stdin=text)


def _rejected(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode != 0, "expected refusal"
    assert "invalid choice: 'spawn'" not in result.stdout, "expected refusal"
    assert "invalid choice: 'spawn'" not in result.stderr, "expected refusal"


def _ok_line(result: subprocess.CompletedProcess[str], line: str) -> None:
    assert result.returncode == 0, result.stderr
    assert line in result.stdout.splitlines()


def test_r14_subject() -> None:
    _ok_line(_parse(_lines(_REQUIRED)), "subject: build-widget")


def test_r15_kind() -> None:
    _ok_line(_parse(_lines(_REQUIRED)), "kind: deliver")


def test_r16_result() -> None:
    _ok_line(_parse(_lines(_REQUIRED)), "result: pass")


def test_r17_revision() -> None:
    _ok_line(_parse(_lines(_REQUIRED)), "revision: abc123def")


def test_r18_evidence() -> None:
    _ok_line(_parse(_lines(_REQUIRED)), "evidence: ran pytest")


def test_r19_missing_subject() -> None:
    reply = _lines([item for item in _REQUIRED if item[0] != "subject"])
    _rejected(_parse(reply))


def test_r20_missing_kind() -> None:
    reply = _lines([item for item in _REQUIRED if item[0] != "kind"])
    _rejected(_parse(reply))


def test_r21_missing_result() -> None:
    reply = _lines([item for item in _REQUIRED if item[0] != "result"])
    _rejected(_parse(reply))


def test_r22_missing_revision() -> None:
    reply = _lines([item for item in _REQUIRED if item[0] != "revision"])
    _rejected(_parse(reply))


def test_r23_missing_evidence() -> None:
    reply = _lines([item for item in _REQUIRED if item[0] != "evidence"])
    _rejected(_parse(reply))


def test_r24_optional_kept() -> None:
    result = _parse(_lines([*_REQUIRED, *_OPTIONAL]))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    for key, value in _OPTIONAL:
        assert f"{key}: {value}" in lines


def test_r25_optional_absent() -> None:
    result = _parse(_lines(_REQUIRED))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    for key, value in _REQUIRED:
        assert f"{key}: {value}" in lines
    for key, _value in _OPTIONAL:
        assert all(not line.startswith(f"{key}:") for line in lines)


def test_r26_message() -> None:
    correction = "Stop and use the phase worktree.\nLeave the frozen oracle untouched.\n"
    result = _run(["spawn", "message"], stdin=correction)
    assert result.returncode == 0, result.stderr
    assert result.stdout == correction


def test_r30_result_enum() -> None:
    reply = _lines([(key, "maybe" if key == "result" else value) for key, value in _REQUIRED])
    _rejected(_parse(reply))


def test_r34_unknown_key() -> None:
    _rejected(_parse(_lines([*_REQUIRED, ("notes", "leftover")])))
