"""Failing oracles for `orchestra spawn render`.

A spec on stdin has subject, brief, orientation, kind, verification,
write_root, and capabilities. Version 1 of the cursor and claude adapters
prints a JSON payload whose prompt sections are Brief, Orientation, Kind,
and Write root, in that order.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from conftest import REPO_ROOT

_HEADERS = ("## Brief", "## Orientation", "## Kind", "## Write root")
_BRIEF = "Line one of the brief.\nLine two stays verbatim.\n"
_ORIENTATION = "Territory: north.\nQuote the requirement verbatim.\n"
_WRITE_ROOT = "/repo/.worktrees/phase-one--build-widget"


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


def _run(
    args: list[str], *, stdin: str | None = None, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    work = cwd
    cleanup = False
    if work is None:
        work = Path(tempfile.mkdtemp(prefix="spawn-oracle-"))
        cleanup = True
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
        if cleanup:
            shutil.rmtree(work, ignore_errors=True)


def _spec(
    *,
    brief: str | None = None,
    orientation: str | None = None,
    kind: str = "deliver",
    verification: bool = False,
    write_root: str | None = None,
    readonly: bool = False,
    extra_capability: str | None = None,
) -> dict[str, object]:
    capabilities: dict[str, object] = {"readonly": readonly}
    if extra_capability is not None:
        capabilities[extra_capability] = True
    return {
        "subject": "build-widget",
        "brief": _BRIEF if brief is None else brief,
        "orientation": _ORIENTATION if orientation is None else orientation,
        "kind": kind,
        "verification": verification,
        "write_root": _WRITE_ROOT if write_root is None else write_root,
        "capabilities": capabilities,
    }


def _render(
    provider: str, body: dict[str, object], *, version: str = "1"
) -> subprocess.CompletedProcess[str]:
    return _run(
        ["spawn", "render", "--provider", provider, "--adapter-version", version],
        stdin=json.dumps(body),
    )


def _rejected(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode != 0
    assert "invalid choice: 'spawn'" not in result.stdout
    assert "invalid choice: 'spawn'" not in result.stderr


def _payload(result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    assert result.returncode == 0, result.stderr
    assert result.stdout.lstrip().startswith("{"), result.stdout
    loaded: object = json.loads(result.stdout)
    assert isinstance(loaded, dict)
    payload: dict[str, object] = {}
    for key, value in loaded.items():
        assert isinstance(key, str)
        payload[key] = value
    return payload


def _prompt(payload: dict[str, object]) -> str:
    prompt = payload.get("prompt")
    assert isinstance(prompt, str)
    cursor = 0
    for header in _HEADERS:
        marker = f"{header}\n"
        found = prompt.find(marker, cursor)
        assert found >= 0
        assert found == 0 or prompt[found - 1] == "\n"
        cursor = found + len(marker)
    return prompt


def _section(prompt: str, header: str, following: str | None) -> str:
    start = prompt.find(f"{header}\n")
    assert start >= 0
    body_start = start + len(header) + 1
    if following is None:
        return prompt[body_start:]
    end = prompt.find(f"\n{following}\n", body_start)
    assert end >= 0
    return prompt[body_start:end]


def _unchanged(section: str, expected: str) -> None:
    assert expected in section
    assert section.strip() == expected.strip()


def _text(body: dict[str, object], key: str) -> str:
    value = body[key]
    assert isinstance(value, str)
    return value


def _kind(prompt: str) -> str:
    return _section(prompt, "## Kind", "## Write root")


def test_r2_cursor_brief() -> None:
    body = _spec(readonly=True)
    payload = _payload(_render("cursor", body))
    prompt = _prompt(payload)
    _unchanged(_section(prompt, "## Brief", "## Orientation"), _text(body, "brief"))
    assert payload.get("readonly") is True


def test_r3_claude_brief() -> None:
    body = _spec(readonly=False)
    payload = _payload(_render("claude", body))
    prompt = _prompt(payload)
    _unchanged(_section(prompt, "## Brief", "## Orientation"), _text(body, "brief"))
    assert "tools" not in payload


def test_r4_cursor_orientation() -> None:
    body = _spec()
    prompt = _prompt(_payload(_render("cursor", body)))
    _unchanged(
        _section(prompt, "## Orientation", "## Kind"),
        _text(body, "orientation"),
    )


def test_r5_claude_orientation() -> None:
    body = _spec()
    prompt = _prompt(_payload(_render("claude", body)))
    _unchanged(
        _section(prompt, "## Orientation", "## Kind"),
        _text(body, "orientation"),
    )


def test_r6_cursor_kind() -> None:
    deliver = _kind(_prompt(_payload(_render("cursor", _spec(verification=False)))))
    assert re.search(r"\bimplement\b", deliver)
    assert "do not edit the tree" not in deliver.casefold()
    verified = _kind(_prompt(_payload(_render("cursor", _spec(verification=True)))))
    assert "do not edit the tree" in verified.casefold()


def test_r7_claude_kind() -> None:
    deliver = _kind(_prompt(_payload(_render("claude", _spec(verification=False)))))
    assert re.search(r"\bimplement\b", deliver)
    assert "do not edit the tree" not in deliver.casefold()
    verified = _kind(_prompt(_payload(_render("claude", _spec(verification=True)))))
    assert "do not edit the tree" in verified.casefold()


def test_r8_cursor_write_root() -> None:
    body = _spec(readonly=False)
    payload = _payload(_render("cursor", body))
    prompt = _prompt(payload)
    _unchanged(_section(prompt, "## Write root", None), _text(body, "write_root"))
    assert payload.get("readonly") is False


def test_r9_claude_write_root() -> None:
    body = _spec(readonly=True)
    payload = _payload(_render("claude", body))
    prompt = _prompt(payload)
    _unchanged(_section(prompt, "## Write root", None), _text(body, "write_root"))
    assert payload.get("tools") == ["Read", "Grep", "Glob"]


def test_r10_cursor_capability() -> None:
    _rejected(_render("cursor", _spec(extra_capability="network")))


def test_r11_claude_capability() -> None:
    _rejected(_render("claude", _spec(extra_capability="network")))


def test_r12_unknown_provider() -> None:
    _rejected(_render("codex", _spec()))


def test_r13_adapter_version() -> None:
    _rejected(_render("cursor", _spec(), version="2"))


def test_r31_empty_brief() -> None:
    _rejected(_render("cursor", _spec(brief="")))


def test_r32_empty_orientation() -> None:
    _rejected(_render("cursor", _spec(orientation="")))


def test_r33_empty_write_root() -> None:
    _rejected(_render("cursor", _spec(write_root="")))
