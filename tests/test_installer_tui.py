"""Questionary prompts on a TTY, and the numbered prompt otherwise."""

from __future__ import annotations

import io
import os
import signal
import sys
import types
from collections.abc import Sequence
from dataclasses import dataclass
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec
from pathlib import Path

import pytest

from installer.matrix import load_matrix
from installer.model import InstallRequest
from installer.paths import is_packaged
from installer.runner import run

REPO_ROOT = Path(__file__).resolve().parents[1]
_HOST_PROMPT = "Select hosts [numbers, ids, ranges, a=all, q=quit]"
_SCOPE_PROMPT = "Scope: [p]roject / [g]lobal"
_MODE_PROMPT = "Mode: [s]ymlink / [c]opy"
_CONFIRM_PROMPT = "Proceed? [Y/n]"
_QUESTIONARY_DEP = "questionary>=2.0,<3"
_MARKER = ".orchestra-install.json"

_CANONICAL_AGENT = """---
name: reviewer
description: Fixture reviewer
---
Fixture reviewer body.
"""


class Choice:
    def __init__(
        self,
        title: str | None = None,
        value: str | None = None,
        disabled: str | None = None,
        checked: bool | None = False,
        shortcut_key: str | bool | None = True,
        description: str | None = None,
    ) -> None:
        self.title = title
        self.disabled = disabled
        self.checked = bool(checked)
        self.shortcut_key = shortcut_key
        self.description = description
        if value is not None:
            self.value = value
        elif isinstance(title, str):
            self.value = title
        else:
            self.value = None


class _Question:
    def __init__(self, answer: object) -> None:
        self.answer = answer
        self.asked = False

    def ask(self) -> object:
        self.asked = True
        return self.answer


@dataclass(frozen=True)
class _Call:
    message: str
    choices: tuple[object, ...]
    default: object
    question: _Question


@dataclass(frozen=True)
class _Script:
    hosts: tuple[str, ...]
    scope: str = "project"
    mode: str = "symlink"
    proceed: bool = True
    cancel: bool = False


class _Fake:
    def __init__(self, script: _Script) -> None:
        self._script = script
        self.checkbox_calls: list[_Call] = []
        self.select_calls: list[_Call] = []
        self.confirm_calls: list[_Call] = []

    def checkbox(
        self,
        message: str,
        choices: Sequence[object] | None = None,
        default: object = None,
        **kwargs: object,
    ) -> _Question:
        question = _Question(None if self._script.cancel else list(self._script.hosts))
        self.checkbox_calls.append(_Call(message, _as_choices(choices, kwargs), default, question))
        return question

    def select(
        self,
        message: str,
        choices: Sequence[object] | None = None,
        default: object = None,
        **kwargs: object,
    ) -> _Question:
        if self._script.cancel:
            answer: object = None
        elif not self.select_calls:
            answer = self._script.scope
        else:
            answer = self._script.mode
        question = _Question(answer)
        self.select_calls.append(_Call(message, _as_choices(choices, kwargs), default, question))
        return question

    def confirm(
        self,
        message: str,
        default: bool = True,
        **kwargs: object,
    ) -> _Question:
        if "default" in kwargs and isinstance(kwargs["default"], bool):
            default = kwargs["default"]
        answer: object = None if self._script.cancel else self._script.proceed
        question = _Question(answer)
        self.confirm_calls.append(_Call(message, (), default, question))
        return question


@dataclass
class _Outcome:
    code: int
    stdout: str
    stderr: str
    prompts: _Fake | None


class _Stream(io.StringIO):
    def __init__(self, text: str = "", *, tty: bool) -> None:
        super().__init__(text)
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


class _QuestionaryBlocker(MetaPathFinder):
    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target: types.ModuleType | None = None,
    ) -> ModuleSpec | None:
        if fullname == "questionary" or fullname.startswith("questionary."):
            raise ModuleNotFoundError(f"No module named {fullname!r}", name=fullname)
        return None


def _as_choices(choices: Sequence[object] | None, kwargs: dict[str, object]) -> tuple[object, ...]:
    picked = choices
    if picked is None and "choices" in kwargs:
        raw = kwargs["choices"]
        if isinstance(raw, str) or not isinstance(raw, Sequence):
            raise AssertionError(f"choices must be a sequence: {raw!r}")
        picked = raw
    if picked is None:
        return ()
    return tuple(picked)


def _choice_value(choice: object) -> str:
    if isinstance(choice, str):
        return choice
    if isinstance(choice, dict):
        raw = choice.get("value", choice.get("name"))
        if isinstance(raw, str):
            return raw
        raise AssertionError(f"choice value is not a string: {choice!r}")
    raw = getattr(choice, "value", None)
    if isinstance(raw, str):
        return raw
    title = getattr(choice, "title", None)
    if isinstance(title, str):
        return title
    raise AssertionError(f"choice value is not a string: {choice!r}")


def _choice_label(choice: object) -> str:
    if isinstance(choice, str):
        return choice
    if isinstance(choice, dict):
        raw = choice.get("name", choice.get("title", ""))
        return raw if isinstance(raw, str) else ""
    title = getattr(choice, "title", None)
    if isinstance(title, str):
        return title
    value = getattr(choice, "value", None)
    return value if isinstance(value, str) else ""


def _choice_checked(choice: object) -> bool:
    if isinstance(choice, str):
        return False
    if isinstance(choice, dict):
        raw = choice.get("checked", False)
        return raw if isinstance(raw, bool) else False
    raw = getattr(choice, "checked", False)
    return raw if isinstance(raw, bool) else False


def _preselected(choices: Sequence[object], default: object) -> tuple[str, ...]:
    token: str | None
    if default is None:
        token = None
    elif isinstance(default, str):
        token = default
    else:
        token = _choice_value(default)
    picked: list[str] = []
    for choice in choices:
        value = _choice_value(choice)
        if _choice_checked(choice) or (token is not None and value == token):
            picked.append(value)
    return tuple(picked)


def _mode_default() -> str:
    return "copy" if is_packaged() else "symlink"


def _make_source(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    skill = source / "skills" / "init"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: init\ndescription: fixture\n---\n",
        encoding="utf-8",
    )
    agents = source / "agents"
    agents.mkdir()
    (agents / "reviewer.prompt.md").write_text(_CANONICAL_AGENT, encoding="utf-8")
    return source


def _prefer_fake_orchestra(monkeypatch: pytest.MonkeyPatch, directory: Path) -> None:
    directory.mkdir()
    program = directory / "orchestra"
    program.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    program.chmod(0o755)
    monkeypatch.setenv("PATH", os.pathsep.join((str(directory), os.environ.get("PATH", ""))))


def _install_questionary(monkeypatch: pytest.MonkeyPatch, script: _Script) -> _Fake:
    fake = _Fake(script)
    module = types.ModuleType("questionary")
    module.checkbox = fake.checkbox
    module.select = fake.select
    module.confirm = fake.confirm
    module.Choice = Choice
    monkeypatch.setitem(sys.modules, "questionary", module)
    return fake


def _block_questionary(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(sys.modules):
        if name == "questionary" or name.startswith("questionary."):
            monkeypatch.delitem(sys.modules, name)
    monkeypatch.setattr(sys, "meta_path", [_QuestionaryBlocker(), *sys.meta_path])


def _on_alarm(signum: int, frame: types.FrameType | None) -> None:
    raise TimeoutError("installer waited for input")


def _bind_stdio(
    monkeypatch: pytest.MonkeyPatch,
    *,
    stdin_text: str,
    stdin_tty: bool,
    stdout_tty: bool,
) -> tuple[_Stream, _Stream]:
    stdout = _Stream(tty=stdout_tty)
    stderr = _Stream(tty=stdout_tty)
    monkeypatch.setattr(sys, "stdin", _Stream(stdin_text, tty=stdin_tty))
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)
    return stdout, stderr


def _drive(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    home: Path,
    project: Path,
    source: Path,
    stdin_text: str,
    stdin_tty: bool,
    stdout_tty: bool,
    script: _Script | None = None,
    interactive: bool = False,
    block_questionary: bool = False,
) -> _Outcome:
    _prefer_fake_orchestra(monkeypatch, tmp_path / "bin")
    prompts: _Fake | None = None
    if block_questionary:
        _block_questionary(monkeypatch)
    elif script is not None:
        prompts = _install_questionary(monkeypatch, script)
    stdout, stderr = _bind_stdio(
        monkeypatch,
        stdin_text=stdin_text,
        stdin_tty=stdin_tty,
        stdout_tty=stdout_tty,
    )
    request = InstallRequest(
        home=home,
        cwd=project,
        source_root=source,
        interactive=interactive,
    )
    previous = signal.signal(signal.SIGALRM, _on_alarm)
    signal.alarm(15)
    try:
        code = run(request)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
    return _Outcome(code, stdout.getvalue(), stderr.getvalue(), prompts)


def _installed(base: Path, scope: str) -> set[str]:
    found: set[str] = set()
    for provider in load_matrix():
        root = provider.global_root if scope == "global" else provider.project_root
        if (base / root / _MARKER).is_file():
            found.add(provider.id)
    return found


def _layout(tmp_path: Path) -> tuple[Path, Path, Path]:
    project = tmp_path / "project"
    project.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    return project, home, _make_source(tmp_path)


def _assert_numbered(stdout: str) -> None:
    assert _HOST_PROMPT in stdout
    assert _SCOPE_PROMPT in stdout
    assert _MODE_PROMPT in stdout
    assert _CONFIRM_PROMPT in stdout


def test_tty_checkbox_hosts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, home, source = _layout(tmp_path)
    outcome = _drive(
        monkeypatch,
        tmp_path,
        home=home,
        project=project,
        source=source,
        stdin_text="1\n\n\n\n",
        stdin_tty=True,
        stdout_tty=True,
        script=_Script(hosts=("cursor",)),
    )
    prompts = outcome.prompts
    assert prompts is not None
    assert prompts.checkbox_calls
    call = prompts.checkbox_calls[0]
    assert call.question.asked
    assert "host" in call.message.casefold()
    providers = load_matrix()
    assert tuple(_choice_value(choice) for choice in call.choices) == tuple(
        provider.id for provider in providers
    )
    for provider, choice in zip(providers, call.choices, strict=True):
        assert provider.name in _choice_label(choice)
    assert outcome.code == 0, outcome.stderr
    assert _installed(home, "project") == {"cursor"}


def test_tty_checks_detected_hosts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, home, source = _layout(tmp_path)
    (home / ".claude").mkdir()
    (home / ".config" / "opencode").mkdir(parents=True)
    detected = ("claude", "opencode")
    outcome = _drive(
        monkeypatch,
        tmp_path,
        home=home,
        project=project,
        source=source,
        stdin_text="\n\n\n\n",
        stdin_tty=True,
        stdout_tty=True,
        script=_Script(hosts=detected),
    )
    prompts = outcome.prompts
    assert prompts is not None
    assert prompts.checkbox_calls
    call = prompts.checkbox_calls[0]
    assert call.question.asked
    assert _preselected(call.choices, call.default) == detected
    providers = load_matrix()
    assert tuple(_choice_value(choice) for choice in call.choices) == tuple(
        provider.id for provider in providers
    )
    assert outcome.code == 0, outcome.stderr
    assert _installed(home, "project") == set(detected)


def test_tty_selects_scope_and_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, home, source = _layout(tmp_path)
    outcome = _drive(
        monkeypatch,
        tmp_path,
        home=home,
        project=project,
        source=source,
        stdin_text="1\n\n\n\n",
        stdin_tty=True,
        stdout_tty=True,
        script=_Script(hosts=("opencode",), scope="global", mode="copy"),
    )
    prompts = outcome.prompts
    assert prompts is not None
    assert len(prompts.select_calls) == 2
    scope, mode = prompts.select_calls
    assert scope.question.asked
    assert mode.question.asked
    assert "scope" in scope.message.casefold()
    assert tuple(_choice_value(choice) for choice in scope.choices) == ("project", "global")
    assert _choice_value(scope.default) == "project"
    assert "mode" in mode.message.casefold()
    assert tuple(_choice_value(choice) for choice in mode.choices) == ("symlink", "copy")
    assert _choice_value(mode.default) == _mode_default()
    assert prompts.confirm_calls
    confirm = prompts.confirm_calls[0]
    assert confirm.question.asked
    assert "proceed" in confirm.message.casefold()
    assert confirm.default is True
    assert outcome.code == 0, outcome.stderr
    assert _installed(home, "global") == {"opencode"}
    assert _installed(home, "project") == set()
    opencode = next(provider for provider in load_matrix() if provider.id == "opencode")
    skill = home / opencode.global_root / "skills" / "init"
    assert skill.is_dir()
    assert not skill.is_symlink()


def test_no_tty_numbered_prompt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, home, source = _layout(tmp_path)
    outcome = _drive(
        monkeypatch,
        tmp_path,
        home=home,
        project=project,
        source=source,
        stdin_text="1\n\n\n\n",
        stdin_tty=False,
        stdout_tty=True,
        script=_Script(hosts=("cursor",)),
        interactive=True,
    )
    prompts = outcome.prompts
    assert prompts is not None
    assert outcome.code == 0, outcome.stderr
    _assert_numbered(outcome.stdout)
    assert prompts.checkbox_calls == []
    assert prompts.select_calls == []
    assert prompts.confirm_calls == []
    assert _installed(home, "project") == {"claude"}


def test_import_failure_numbered_prompt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, home, source = _layout(tmp_path)
    outcome = _drive(
        monkeypatch,
        tmp_path,
        home=home,
        project=project,
        source=source,
        stdin_text="1\n\n\n\n",
        stdin_tty=True,
        stdout_tty=True,
        block_questionary=True,
    )
    assert outcome.code == 0, outcome.stderr
    _assert_numbered(outcome.stdout)
    assert "questionary" not in sys.modules
    assert _installed(home, "project") == {"claude"}


def test_cancel_exits_without_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, home, source = _layout(tmp_path)
    outcome = _drive(
        monkeypatch,
        tmp_path,
        home=home,
        project=project,
        source=source,
        stdin_text="1\n\n\n\n",
        stdin_tty=True,
        stdout_tty=True,
        script=_Script(hosts=("cursor",), cancel=True),
    )
    assert outcome.code == 0, outcome.stderr
    assert list(home.iterdir()) == []


def test_pyproject_declares_questionary() -> None:
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    project = text.split("[dependency-groups]", 1)[0]
    body = project.split("dependencies = [", 1)
    assert len(body) == 2
    block = body[1].split("]", 1)[0]
    declared = [line.strip().strip(",").strip("\"'") for line in block.splitlines() if line.strip()]
    assert _QUESTIONARY_DEP in declared
