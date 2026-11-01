"""README Install section leads with the published install commands."""

from __future__ import annotations

import re

from conftest import REPO_ROOT

_UVX_INSTALL = "uvx --from git+https://github.com/andrewy1n/orchestra orchestra install"
_CURL_INSTALL = (
    "curl -fsSL https://raw.githubusercontent.com/andrewy1n/orchestra/main/install.sh | sh"
)
_BASH_FENCE: re.Pattern[str] = re.compile(r"```bash\n(.*?)```", re.DOTALL)
_CURSOR_END: re.Pattern[str] = re.compile(r"\n#{1,3}(?!#) ")
_SENTENCE_END: re.Pattern[str] = re.compile(r"(?<=[.!?])\s+")
_COPY_SCRIPT = "".join(("sync-", "plugin"))


def _readme() -> str:
    return (REPO_ROOT / "README.md").read_text(encoding="utf-8")


def _install_section() -> str:
    text = _readme()
    marker = "\n## Install\n"
    rest = text[text.index(marker) + len(marker) :]
    end = rest.find("\n## ")
    return rest if end < 0 else rest[:end]


def _fenced_bash_commands(section: str) -> list[str]:
    commands: list[str] = []
    for body in _BASH_FENCE.findall(section):
        commands.extend(line.strip() for line in body.splitlines() if line.strip())
    return commands


def _cursor_section() -> str:
    text = _readme()
    marker = "\n### Cursor\n"
    rest = text[text.index(marker) + len(marker) :]
    match = _CURSOR_END.search(rest)
    return rest if match is None else rest[: match.start()]


def test_install_opens_with_uvx() -> None:
    commands = _fenced_bash_commands(_install_section())
    assert commands[:1] == [_UVX_INSTALL]


def test_curl_script_is_second() -> None:
    commands = _fenced_bash_commands(_install_section())
    assert commands[1:2] == [_CURL_INSTALL]


def test_claude_marketplace_commands() -> None:
    text = _readme()
    assert "claude plugin marketplace add andrewy1n/orchestra" in text
    assert "claude plugin install orchestra@orchestra -y" in text


def test_installer_puts_cli_on_path() -> None:
    folded = re.sub(r"\s+", " ", _install_section())
    claim = [
        sentence
        for sentence in _SENTENCE_END.split(folded)
        if "orchestra" in sentence and "canon" in sentence and "missing" in sentence
    ]
    assert claim


def test_cursor_section_has_no_copy_script() -> None:
    section = _cursor_section()
    assert "orchestra install" in section
    assert _COPY_SCRIPT not in section
