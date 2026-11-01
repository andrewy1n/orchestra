"""Prompts for the installer wizard."""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from types import ModuleType
from typing import Protocol, TextIO, TypeGuard

from installer.detect import HostStatus
from installer.model import InstallRequest

InputFn = Callable[[str], str]


class WizardCancelled(Exception):
    """The user asked to quit, or the prompt reached EOF."""


class WizardSelectionError(ValueError):
    """A host selection token could not be resolved."""


def _stdin_isatty() -> bool:
    return sys.stdin.isatty()


def _stdout_isatty() -> bool:
    return sys.stdout.isatty()


class _Answer(Protocol):
    def ask(self) -> object: ...


class _ChoiceFactory(Protocol):
    def __call__(
        self,
        title: str,
        value: str | None = None,
        *,
        checked: bool = False,
    ) -> object: ...


class _RichPrompts(Protocol):
    Choice: _ChoiceFactory

    def checkbox(self, message: str, *, choices: Sequence[object]) -> _Answer: ...

    def select(
        self,
        message: str,
        *,
        choices: Sequence[str],
        default: str,
    ) -> _Answer: ...

    def confirm(self, message: str, *, default: bool) -> _Answer: ...


def _module_is_rich(module: ModuleType) -> TypeGuard[_RichPrompts]:
    return (
        callable(getattr(module, "checkbox", None))
        and callable(getattr(module, "select", None))
        and callable(getattr(module, "confirm", None))
        and callable(getattr(module, "Choice", None))
    )


def _rich_prompts() -> _RichPrompts | None:
    if not (_stdin_isatty() and _stdout_isatty()):
        return None
    try:
        module = importlib.import_module("questionary")
    except ImportError:
        return None
    if _module_is_rich(module):
        return module
    return None


def _refuse_cancel(answer: object) -> object:
    if answer is None:
        raise WizardCancelled("cancelled")
    return answer


def _questionary_hosts(
    prompts: _RichPrompts,
    statuses: tuple[HostStatus, ...],
    default_ids: tuple[str, ...],
) -> tuple[str, ...]:
    defaults = set(default_ids)
    choices = [
        prompts.Choice(
            f"{status.provider.name} ({status.provider.id})",
            value=status.provider.id,
            checked=status.provider.id in defaults,
        )
        for status in statuses
    ]
    answer = _refuse_cancel(prompts.checkbox("Select hosts", choices=choices).ask())
    if isinstance(answer, str) or not isinstance(answer, Sequence):
        raise WizardSelectionError("select at least one host")
    allowed = set(_provider_ids(statuses))
    selected: list[str] = []
    for item in answer:
        if not isinstance(item, str) or item not in allowed:
            raise WizardSelectionError("select at least one host")
        if item not in selected:
            selected.append(item)
    if not selected:
        raise WizardSelectionError("select at least one host")
    return tuple(selected)


def _questionary_choice(
    prompts: _RichPrompts,
    message: str,
    choices: tuple[str, ...],
    default: str,
) -> str:
    answer = _refuse_cancel(prompts.select(message, choices=choices, default=default).ask())
    if isinstance(answer, str) and answer in choices:
        return answer
    raise WizardSelectionError(f"unknown selection: {answer!r}")


def _questionary_confirm(prompts: _RichPrompts, question: str, default: bool) -> bool:
    answer = _refuse_cancel(prompts.confirm(question, default=default).ask())
    if isinstance(answer, bool):
        return answer
    raise WizardSelectionError("answer yes or no")


def wants_wizard(request: InstallRequest) -> bool:
    """Whether this request should run the interactive install wizard."""
    if request.list_only or request.uninstall:
        return False
    if request.non_interactive:
        return False
    if request.interactive:
        return True
    return _stdin_isatty() and _stdout_isatty()


def _ask(prompt: str, input_fn: InputFn) -> str:
    try:
        return input_fn(prompt)
    except EOFError as exc:
        raise WizardCancelled("cancelled") from exc


def _provider_ids(statuses: tuple[HostStatus, ...]) -> tuple[str, ...]:
    return tuple(status.provider.id for status in statuses)


def parse_host_selection(text: str, statuses: tuple[HostStatus, ...]) -> tuple[str, ...]:
    """Resolve numbers, ids, ranges, ``a``/``all``, and ``q``/``quit``."""
    value = text.strip()
    if not value:
        raise WizardSelectionError("select at least one host")

    tokens = value.replace(",", " ").split()
    ids = _provider_ids(statuses)
    by_id = set(ids)
    selected: list[str] = []

    def add(provider_id: str) -> None:
        if provider_id not in selected:
            selected.append(provider_id)

    for token in tokens:
        lowered = token.lower()
        if lowered in ("q", "quit"):
            raise WizardCancelled("cancelled")
        if lowered in ("a", "all"):
            return ids
        if lowered in by_id:
            add(lowered)
            continue
        if lowered.isdigit():
            index = int(lowered)
            if not 1 <= index <= len(statuses):
                raise WizardSelectionError(f"host number out of range: {token}")
            add(ids[index - 1])
            continue
        if "-" in lowered or ".." in lowered:
            separator = ".." if ".." in lowered else "-"
            start_text, _, end_text = lowered.partition(separator)
            if not (start_text.isdigit() and end_text.isdigit()):
                raise WizardSelectionError(f"invalid host range: {token}")
            start, end = int(start_text), int(end_text)
            if start > end or start < 1 or end > len(statuses):
                raise WizardSelectionError(f"host range out of range: {token}")
            for index in range(start, end + 1):
                add(ids[index - 1])
            continue
        raise WizardSelectionError(f"unknown host: {token}")

    if not selected:
        raise WizardSelectionError("select at least one host")
    return tuple(selected)


def prompt_hosts(
    statuses: tuple[HostStatus, ...],
    default_ids: tuple[str, ...] = (),
    *,
    input_fn: InputFn = input,
    output: TextIO = sys.stdout,
) -> tuple[str, ...]:
    """Render the host matrix and loop until a valid selection is made."""
    prompts = _rich_prompts()
    if prompts is not None:
        return _questionary_hosts(prompts, statuses, default_ids)
    print("Detected hosts:", file=output)
    for index, status in enumerate(statuses, 1):
        project = "yes" if status.project else "no"
        global_ = "yes" if status.global_ else "no"
        print(
            f"  [{index}] {status.provider.name} ({status.provider.id})"
            f"   project: {project}   global: {global_}",
            file=output,
        )
    default_text = ",".join(default_ids) if default_ids else "none"
    prompt = f"Select hosts [numbers, ids, ranges, a=all, q=quit] (default: {default_text}): "
    while True:
        answer = _ask(prompt, input_fn)
        if not answer.strip():
            if default_ids:
                return tuple(default_ids)
            raise WizardSelectionError("no hosts detected; select a host explicitly or use --all")
        try:
            return parse_host_selection(answer, statuses)
        except WizardSelectionError as exc:
            print(f"  {exc}", file=output)


def prompt_scope(
    default: str = "project",
    *,
    input_fn: InputFn = input,
    output: TextIO = sys.stdout,
    project_base: Path | None = None,
    global_base: Path | None = None,
) -> str:
    """Prompt for project or global scope, defaulting to project."""
    if default not in ("project", "global"):
        default = "project"
    prompts = _rich_prompts()
    if prompts is not None:
        choice = _questionary_choice(prompts, "Scope", ("project", "global"), default)
        if project_base is not None and global_base is not None:
            base = project_base if choice == "project" else global_base
            print(f"Base: {base}", file=output)
        return choice
    while True:
        answer = _ask(
            f"Scope: [p]roject / [g]lobal (default: {default}): ",
            input_fn,
        )
        value = answer.strip().lower()
        if not value:
            choice = default
        elif value in ("p", "project"):
            choice = "project"
        elif value in ("g", "global"):
            choice = "global"
        else:
            print("  choose project or global", file=output)
            continue
        if project_base is not None and global_base is not None:
            base = project_base if choice == "project" else global_base
            print(f"Base: {base}", file=output)
        return choice


def prompt_mode(
    default: str = "symlink",
    *,
    input_fn: InputFn = input,
    output: TextIO = sys.stdout,
) -> str:
    """Prompt for symlink or copy mode, defaulting to symlink."""
    if default not in ("symlink", "copy"):
        default = "symlink"
    prompts = _rich_prompts()
    if prompts is not None:
        choice = _questionary_choice(prompts, "Mode", ("symlink", "copy"), default)
        print(f"Mode: {choice}", file=output)
        return choice
    while True:
        answer = _ask(
            f"Mode: [s]ymlink / [c]opy (default: {default}): ",
            input_fn,
        )
        value = answer.strip().lower()
        if not value:
            choice = default
        elif value in ("s", "symlink"):
            choice = "symlink"
        elif value in ("c", "copy"):
            choice = "copy"
        else:
            print("  choose symlink or copy", file=output)
            continue
        print(f"Mode: {choice}", file=output)
        return choice


def confirm(
    question: str,
    default: bool = True,
    *,
    input_fn: InputFn = input,
    output: TextIO = sys.stdout,
) -> bool:
    """Ask a yes/no question; a blank answer uses ``default``."""
    prompts = _rich_prompts()
    if prompts is not None:
        return _questionary_confirm(prompts, question, default)
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        answer = _ask(f"{question} {suffix}: ", input_fn)
        value = answer.strip().lower()
        if not value:
            return default
        if value in ("y", "yes"):
            return True
        if value in ("n", "no"):
            return False
        print("  answer yes or no", file=output)
