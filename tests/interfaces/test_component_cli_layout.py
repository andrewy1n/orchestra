"""Pin which component owns each command group's parser and handlers."""

from __future__ import annotations

import argparse
import importlib
from dataclasses import dataclass

import pytest

import orchestra.cli as root_cli


@dataclass(frozen=True)
class Group:
    name: str
    component_cli: str
    verbs: tuple[str, ...]
    root_handlers: tuple[str, ...]


CONDUCTOR_SUITE_GATE = Group(
    "conductor_suite_gate",
    "orchestra.conductor.cli",
    ("suite", "gate", "analyze", "review-brief"),
    (
        "_cmd_suite_policy",
        "_cmd_suite_start",
        "_cmd_suite_poll",
        "_cmd_suite_collect",
        "_cmd_suite_record",
        "_cmd_suite_cancel",
        "_cmd_gate",
        "_cmd_analyze",
        "_cmd_review_brief",
    ),
)

GROUPS = [CONDUCTOR_SUITE_GATE]


def _registered_verbs(component_cli: str) -> set[str]:
    module = importlib.import_module(component_cli)
    parser = argparse.ArgumentParser(prog="orchestra")
    sub = parser.add_subparsers(dest="command")
    module.add_parsers(sub)
    return set(sub.choices)


@pytest.mark.parametrize("group", GROUPS, ids=[group.name for group in GROUPS])
def test_component_cli_registers_its_verbs(group: Group) -> None:
    assert group.verbs
    assert set(group.verbs) <= _registered_verbs(group.component_cli)


@pytest.mark.parametrize("group", GROUPS, ids=[group.name for group in GROUPS])
def test_root_cli_defines_no_handlers_for_moved_verbs(group: Group) -> None:
    defined_here = [
        name
        for name in group.root_handlers
        if getattr(getattr(root_cli, name, None), "__module__", None) == root_cli.__name__
    ]
    assert defined_here == []
