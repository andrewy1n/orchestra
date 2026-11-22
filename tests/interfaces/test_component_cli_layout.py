"""Pin which component owns each command group's parser and handlers."""

from __future__ import annotations

import argparse
import ast
import importlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path

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

CONDUCTOR_WAVE_TASK = Group(
    "conductor_wave_task",
    "orchestra.conductor.cli",
    ("wave", "task"),
    (
        "_cmd_wave_start",
        "_cmd_wave_end",
        "_cmd_wave_resolve",
        "_cmd_task_land",
        "_cmd_task_redispatch",
    ),
)

CONDUCTOR_LAND_CLOSE = Group(
    "conductor_land_close",
    "orchestra.conductor.cli",
    ("land", "close", "close-batch"),
    ("_cmd_land", "_cmd_close"),
)

CONDUCTOR_WORKFLOW = Group(
    "conductor_workflow",
    "orchestra.conductor.cli",
    ("workflow",),
    ("_cmd_workflow",),
)

LIGHT_COMPONENTS_COMPOSER = Group(
    "light_components_composer",
    "orchestra.composer.cli",
    ("idea", "place"),
    ("_cmd_idea", "_cmd_place"),
)

LIGHT_COMPONENTS_SCORE = Group(
    "light_components_score",
    "orchestra.score.cli",
    ("effort",),
    ("_cmd_effort_autonomy",),
)

LIGHT_COMPONENTS_METRICS = Group(
    "light_components_metrics",
    "orchestra.metrics.cli",
    ("metrics",),
    (),
)

LIGHT_COMPONENTS_SESSIONS = Group(
    "light_components_sessions",
    "orchestra.sessions.cli",
    ("sessions",),
    (),
)

LIGHT_COMPONENTS = [
    LIGHT_COMPONENTS_COMPOSER,
    LIGHT_COMPONENTS_SCORE,
    LIGHT_COMPONENTS_METRICS,
    LIGHT_COMPONENTS_SESSIONS,
]

TUNER_CANON_STAGE_TUNER = Group(
    "tuner_canon_stage_tuner",
    "orchestra.tuner.cli",
    ("verify", "plugins"),
    ("_cmd_plugins",),
)

TUNER_CANON_STAGE_CONDUCTOR = Group(
    "tuner_canon_stage_conductor",
    "orchestra.conductor.cli",
    ("check",),
    ("_cmd_check",),
)

TUNER_CANON_STAGE_CANON = Group(
    "tuner_canon_stage_canon",
    "orchestra.canon.cli",
    ("store",),
    (
        "_cmd_store_path",
        "_cmd_store_scan",
        "_cmd_store_run",
        "_cmd_store_ensure",
        "_dispatch_store",
    ),
)

TUNER_CANON_STAGE_STAGE = Group(
    "tuner_canon_stage_stage",
    "orchestra.stage.cli",
    ("install", "hook-start", "hook-stop"),
    ("_cmd_install",),
)

TUNER_CANON_STAGE = [
    TUNER_CANON_STAGE_TUNER,
    TUNER_CANON_STAGE_CONDUCTOR,
    TUNER_CANON_STAGE_CANON,
    TUNER_CANON_STAGE_STAGE,
]

VIEWS = Group(
    "views",
    "orchestra.views.cli",
    ("handoff", "view", "brief"),
    (),
)

GROUPS = [
    CONDUCTOR_SUITE_GATE,
    CONDUCTOR_WAVE_TASK,
    CONDUCTOR_LAND_CLOSE,
    CONDUCTOR_WORKFLOW,
    *LIGHT_COMPONENTS,
    *TUNER_CANON_STAGE,
    VIEWS,
]


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


def test_conductor_workflow_cli_module_is_gone_from_the_root_package() -> None:
    assert importlib.util.find_spec("orchestra.workflow_cli") is None


def test_conductor_workflow_is_a_conductor_command() -> None:
    conductor_cli = importlib.import_module("orchestra.conductor.cli")
    assert "workflow" in conductor_cli.COMMANDS


@pytest.mark.parametrize("group", LIGHT_COMPONENTS, ids=[group.name for group in LIGHT_COMPONENTS])
def test_light_components_cli_owns_its_commands_and_runs_them(group: Group) -> None:
    module = importlib.import_module(group.component_cli)
    assert set(group.verbs) == set(module.COMMANDS)
    assert callable(module.run)


def test_light_components_metrics_cli_module_is_gone_from_the_root_package() -> None:
    assert importlib.util.find_spec("orchestra.metrics_cli") is None


EXCLUSIVE = [g for g in TUNER_CANON_STAGE if g is not TUNER_CANON_STAGE_CONDUCTOR]


@pytest.mark.parametrize("group", EXCLUSIVE, ids=[group.name for group in EXCLUSIVE])
def test_tuner_canon_stage_cli_owns_its_commands_and_runs_them(group: Group) -> None:
    module = importlib.import_module(group.component_cli)
    assert set(group.verbs) == set(module.COMMANDS)
    assert callable(module.run)


@pytest.mark.parametrize(
    "module",
    ["orchestra.store", "orchestra.plugin_cli", "orchestra.plugin_verify_cli"],
)
def test_tuner_canon_stage_module_is_gone_from_the_root_package(module: str) -> None:
    assert importlib.util.find_spec(module) is None


def test_tuner_canon_stage_root_cli_defines_no_cmd_handlers() -> None:
    tree = ast.parse(Path(root_cli.__file__).read_text(encoding="utf-8"))
    handlers = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("_cmd_")
    ]
    assert handlers == []


def test_tuner_canon_stage_conductor_cli_owns_check() -> None:
    module = importlib.import_module("orchestra.conductor.cli")
    assert "check" in module.COMMANDS


def test_views_cli_owns_its_commands_and_runs_them() -> None:
    module = importlib.import_module(VIEWS.component_cli)
    assert set(VIEWS.verbs) == set(module.COMMANDS)
    assert callable(module.run)


def test_views_status_registers_status_where_it_lives() -> None:
    module = importlib.import_module("orchestra.views.status")
    parser = argparse.ArgumentParser(prog="orchestra")
    sub = parser.add_subparsers(dest="command")
    module.add_parser(sub)
    assert "status" in sub.choices
    assert callable(module.run)


def test_views_is_a_package_not_a_module_file() -> None:
    spec = importlib.util.find_spec("orchestra.views")
    assert spec is not None
    assert spec.submodule_search_locations is not None


@pytest.mark.parametrize("module", ["orchestra.view_cli", "orchestra.status_cli"])
def test_views_root_cli_module_is_gone_from_the_root_package(module: str) -> None:
    assert importlib.util.find_spec(module) is None


def test_views_render_module_is_in_the_package() -> None:
    assert importlib.util.find_spec("orchestra.views.render") is not None


@pytest.mark.parametrize("attribute", ["view_cli", "status_cli"])
def test_views_root_cli_does_not_import_the_old_modules(attribute: str) -> None:
    assert not hasattr(root_cli, attribute)
