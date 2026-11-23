"""Pin which component owns each command group's parser and handlers."""

from __future__ import annotations

import argparse
import ast
import importlib
import importlib.util
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import pytest
from test_boundaries import COMPONENTS

import orchestra.cli as root_cli
from orchestra.tools import command_kit

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


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


def _injected(module_name: str) -> dict[str, object]:
    if module_name == "orchestra.canon.cli":
        return {"scan": lambda _records: [], "recover": lambda _project, _apply: None}
    if module_name == "orchestra.conductor.cli":
        return {"render_brief": lambda _subject, _records: ""}
    return {}


def _commands(module: ModuleType) -> list[command_kit.Command]:
    return module.commands(**_injected(module.__name__))


def _declared_verbs(module: ModuleType) -> set[str]:
    return {command.name for command in _commands(module)}


def _registered_verbs(component_cli: str) -> set[str]:
    module = importlib.import_module(component_cli)
    parser = argparse.ArgumentParser(prog="orchestra")
    sub = parser.add_subparsers(dest="command")
    command_kit.mount(sub, _commands(module))
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
    assert "workflow" in _declared_verbs(conductor_cli)


@pytest.mark.parametrize("group", LIGHT_COMPONENTS, ids=[group.name for group in LIGHT_COMPONENTS])
def test_light_components_cli_owns_its_commands_and_runs_them(group: Group) -> None:
    module = importlib.import_module(group.component_cli)
    assert set(group.verbs) == _declared_verbs(module)


def test_light_components_metrics_cli_module_is_gone_from_the_root_package() -> None:
    assert importlib.util.find_spec("orchestra.metrics_cli") is None


EXCLUSIVE = [g for g in TUNER_CANON_STAGE if g is not TUNER_CANON_STAGE_CONDUCTOR]


@pytest.mark.parametrize("group", EXCLUSIVE, ids=[group.name for group in EXCLUSIVE])
def test_tuner_canon_stage_cli_owns_its_commands_and_runs_them(group: Group) -> None:
    module = importlib.import_module(group.component_cli)
    assert set(group.verbs) == _declared_verbs(module)
    assert hasattr(module, "commands") or callable(module.run)


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
    assert "check" in _declared_verbs(module)


def test_views_cli_owns_its_commands_and_runs_them() -> None:
    module = importlib.import_module(VIEWS.component_cli)
    assert set(VIEWS.verbs) == _declared_verbs(module)


def test_views_status_registers_status_where_it_lives() -> None:
    module = importlib.import_module("orchestra.views.status")
    parser = argparse.ArgumentParser(prog="orchestra")
    sub = parser.add_subparsers(dest="command")
    command_kit.mount(sub, module.commands())
    assert "status" in sub.choices


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


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT_CLI_SOURCE = Path(root_cli.__file__).read_text(encoding="utf-8")
ROOT_ALLOWED_FUNCTIONS = {"_build_parser", "main"}
ROOT_ALLOWED_KIT_IMPORTS = {"orchestra.tools.command_kit"}
ROOT_OPTION_CALLS = {"add_argument", "add_argument_group", "add_mutually_exclusive_group"}
ROOT_REGISTER_CALLS = {"add_parsers", "add_parser", "commands"}
CLI_COMPONENTS = (
    "conductor",
    "composer",
    "score",
    "metrics",
    "sessions",
    "stage",
    "tuner",
    "canon",
    "views",
)
COMPONENT_STATUS_MODULE = "orchestra.views.status"


def _component_cli_modules(tree: ast.Module) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.level or not node.module:
            continue
        for alias in node.names:
            module = f"{node.module}.{alias.name}"
            local = alias.asname or alias.name
            parts = module.split(".")
            is_cli = len(parts) == 3 and parts[0] == "orchestra" and parts[2] == "cli"
            if is_cli or module == COMPONENT_STATUS_MODULE:
                aliases[local] = module
    return aliases


def root_composes_violations(source: str) -> list[str]:
    tree = ast.parse(source)
    aliases = _component_cli_modules(tree)
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            name = getattr(node, "name", "<lambda>")
            if name not in ROOT_ALLOWED_FUNCTIONS:
                found.append(f"function {name} at line {node.lineno}")
        elif isinstance(node, ast.ClassDef):
            found.append(f"class {node.name} at line {node.lineno}")
        elif (
            isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("orchestra")
        ):
            for alias in node.names:
                module = f"{node.module}.{alias.name}"
                if module in ROOT_ALLOWED_KIT_IMPORTS:
                    continue
                if (alias.asname or alias.name) not in aliases or aliases[
                    alias.asname or alias.name
                ] != module:
                    found.append(f"import {module} at line {node.lineno}")
        elif isinstance(node, ast.Import):
            found.extend(
                f"import {alias.name} at line {node.lineno}"
                for alias in node.names
                if alias.name.startswith("orchestra")
            )
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ROOT_OPTION_CALLS:
                found.append(f"option definition {node.func.attr} at line {node.lineno}")
    mounted: set[str] = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        owner = node.func.value
        if node.func.attr in ROOT_REGISTER_CALLS:
            if node.func.attr == "commands" and isinstance(owner, ast.Name) and owner.id in aliases:
                mounted.add(owner.id)
            else:
                found.append(f"verb registered outside a component at line {node.lineno}")
        elif node.func.attr == "run" and isinstance(owner, ast.Name) and owner.id in aliases:
            found.append(f"{owner.id}.run is called by the root at line {node.lineno}")
    for alias in sorted(set(aliases) - mounted):
        found.append(f"{alias} is imported but its commands are not mounted")
    return found


def test_root_composes_real_root_cli_holds_only_composition_and_dispatch() -> None:
    assert root_composes_violations(ROOT_CLI_SOURCE) == []


def test_root_composes_checker_flags_a_seeded_handler() -> None:
    seeded = ROOT_CLI_SOURCE + "\n\ndef _cmd_seeded(args):\n    return 0\n"
    line = len(ROOT_CLI_SOURCE.splitlines()) + 3
    assert f"function _cmd_seeded at line {line}" in root_composes_violations(seeded)


def test_root_composes_checker_flags_a_seeded_store_import() -> None:
    seeded = "from orchestra.canon.project import Project\n" + ROOT_CLI_SOURCE
    assert any(
        "orchestra.canon.project.Project" in line for line in root_composes_violations(seeded)
    )


def test_root_composes_checker_flags_a_seeded_option_definition() -> None:
    seeded = ROOT_CLI_SOURCE.replace(
        "    return parser\n", "    parser.add_argument('--x')\n    return parser\n", 1
    )
    assert any(
        "option definition add_argument" in line for line in root_composes_violations(seeded)
    )


def test_root_composes_checker_flags_a_seeded_root_owned_verb() -> None:
    seeded = ROOT_CLI_SOURCE.replace(
        "    return parser\n", "    sub.add_parser('own', help='x')\n    return parser\n", 1
    )
    assert any(
        "verb registered outside a component" in line for line in root_composes_violations(seeded)
    )


def test_root_composes_checker_flags_a_component_that_is_not_mounted() -> None:
    seeded = ROOT_CLI_SOURCE.replace(
        "    command_kit.mount(sub, canon_cli.commands(scan=scan, recover=recover))\n", ""
    )
    assert "canon_cli is imported but its commands are not mounted" in root_composes_violations(
        seeded
    )


def test_root_composes_checker_flags_a_component_run_call() -> None:
    seeded = ROOT_CLI_SOURCE.replace(
        "return command_kit.run(args, extra)", "return canon_cli.run(args)"
    )
    assert any(
        "canon_cli.run is called by the root" in line for line in root_composes_violations(seeded)
    )


def _own_registered_verbs(module_name: str) -> set[str]:
    module = importlib.import_module(module_name)
    parser = argparse.ArgumentParser(prog="orchestra")
    sub = parser.add_subparsers(dest="command")
    command_kit.mount(sub, _commands(module))
    return set(sub.choices)


def test_every_component_has_a_cli_module_with_the_contract() -> None:
    for component in CLI_COMPONENTS:
        module = importlib.import_module(f"orchestra.{component}.cli")
        assert _commands(module), component
        for legacy in ("add_parsers", "COMMANDS", "run"):
            assert not hasattr(module, legacy), (component, legacy)


def test_every_component_registers_exactly_its_own_commands() -> None:
    for component in CLI_COMPONENTS:
        module = importlib.import_module(f"orchestra.{component}.cli")
        assert _own_registered_verbs(f"orchestra.{component}.cli") == _declared_verbs(module), (
            component
        )


def test_every_component_verb_is_registered_by_one_component_only() -> None:
    owners: dict[str, list[str]] = {}
    for component in CLI_COMPONENTS:
        module = importlib.import_module(f"orchestra.{component}.cli")
        for verb in _declared_verbs(module):
            owners.setdefault(verb, []).append(component)
    owners.setdefault("status", []).append("views.status")
    assert {verb: names for verb, names in owners.items() if len(names) > 1} == {}


def test_every_component_command_union_covers_every_root_parser_verb() -> None:
    parser = root_cli._build_parser()
    actions = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)]
    assert len(actions) == 1
    built = set(actions[0].choices)
    union = {"verify", "status"}
    for component in CLI_COMPONENTS:
        union |= _declared_verbs(importlib.import_module(f"orchestra.{component}.cli"))
    assert built <= union
    assert union <= built


def test_every_component_package_directory_is_listed_in_pyproject_packages() -> None:
    with (REPO_ROOT / "pyproject.toml").open("rb") as stream:
        listed = set(tomllib.load(stream)["tool"]["setuptools"]["packages"])
    on_disk = {
        ".".join(path.parent.relative_to(REPO_ROOT).parts)
        for path in (REPO_ROOT / "orchestra").rglob("__init__.py")
    }
    assert on_disk - listed == set()


def test_every_component_in_the_boundary_list_that_owns_verbs_has_a_cli_module() -> None:
    owns_no_verbs = {"tools"}
    for component in COMPONENTS:
        if component in owns_no_verbs:
            continue
        assert importlib.util.find_spec(f"orchestra.{component}.cli") is not None, component


CLI_MODULE_FILES = (
    *(f"orchestra/{component}/cli.py" for component in CLI_COMPONENTS if component != "conductor"),
    *(
        path.relative_to(REPO_ROOT).as_posix()
        for path in sorted((REPO_ROOT / "orchestra/conductor/cli").glob("*.py"))
    ),
    "orchestra/views/status.py",
    "orchestra/canon/store_commands.py",
    "orchestra/tuner/verify_plugins.py",
)
CANON_PROGRAM = "orchestra/canon/cli.py"
NAME_GUARD_FILES = tuple(path for path in CLI_MODULE_FILES if path != CANON_PROGRAM)
STORE_NOT_READY_ALLOWED = {"orchestra/stage/hooks.py", CANON_PROGRAM}
STORE_NOT_READY_FILES = tuple(
    path for path in CLI_MODULE_FILES if path not in STORE_NOT_READY_ALLOWED
)
LEGACY_MODULE_NAMES = ("COMMANDS", "add_parsers", "PASSTHROUGH")


def _is_command_ref(node: ast.expr) -> bool:
    return (isinstance(node, ast.Attribute) and node.attr == "command") or (
        isinstance(node, ast.Name) and node.id == "command"
    )


def _is_command_test(node: ast.expr) -> bool:
    if not isinstance(node, ast.Compare) or not _is_command_ref(node.left):
        return False
    if not all(isinstance(op, (ast.Eq, ast.In)) for op in node.ops):
        return False
    return all(
        isinstance(item, (ast.Constant, ast.Set, ast.Tuple, ast.List)) for item in node.comparators
    )


def _is_name_set(value: ast.expr | None) -> bool:
    if isinstance(value, ast.Set):
        return bool(value.elts) and all(isinstance(e, ast.Constant) for e in value.elts)
    if (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id in {"frozenset", "set"}
        and len(value.args) == 1
    ):
        return _is_name_set(value.args[0]) or (
            isinstance(value.args[0], (ast.Tuple, ast.List))
            and bool(value.args[0].elts)
            and all(isinstance(e, ast.Constant) for e in value.args[0].elts)
        )
    return False


def command_name_violations(source: str) -> list[str]:
    tree = ast.parse(source)
    found: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and _is_name_set(node.value):
            found.append(f"command name set at line {node.lineno}")
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and _is_command_test(node.test):
            chained = len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If)
            if chained and _is_command_test(node.orelse[0].test):  # type: ignore[attr-defined]
                found.append(f"command dispatch chain at line {node.lineno}")
        elif isinstance(node, ast.ClassDef):
            declares_add_parser = any(
                isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                and item.name == "add_parser"
                for item in node.body
            )
            if node.name == "SubparserGroup" or declares_add_parser:
                found.append(f"local subparser protocol {node.name} at line {node.lineno}")
    return found


def _catches_store_not_ready(handler: ast.ExceptHandler) -> bool:
    def named(node: ast.expr) -> bool:
        return (isinstance(node, ast.Name) and node.id == "StoreNotReady") or (
            isinstance(node, ast.Attribute) and node.attr == "StoreNotReady"
        )

    caught = handler.type
    if caught is None:
        return False
    if isinstance(caught, ast.Tuple):
        return any(named(item) for item in caught.elts)
    return named(caught)


def store_not_ready_violations(source: str) -> list[str]:
    return [
        f"except StoreNotReady at line {node.lineno}"
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ExceptHandler) and _catches_store_not_ready(node)
    ]


def _real_violations(
    files: tuple[str, ...], check: Callable[[str], list[str]]
) -> dict[str, list[str]]:
    found = {path: check((REPO_ROOT / path).read_text(encoding="utf-8")) for path in files}
    return {path: lines for path, lines in found.items() if lines}


def test_every_component_cli_module_exports_commands_and_no_legacy_names() -> None:
    modules = [
        importlib.import_module(f"orchestra.{component}.cli") for component in CLI_COMPONENTS
    ]
    modules.append(importlib.import_module(COMPONENT_STATUS_MODULE))
    for module in modules:
        assert callable(getattr(module, "commands", None)), module.__name__
        tree = ast.parse(Path(module.__file__ or "").read_text(encoding="utf-8"))
        top_level = {
            target.id
            for node in tree.body
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
            if isinstance(target, ast.Name)
        } | {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for legacy in (*LEGACY_MODULE_NAMES, "run"):
            assert legacy not in top_level, (module.__name__, legacy)
            assert not hasattr(module, legacy), (module.__name__, legacy)


def test_every_component_declares_each_command_name_exactly_once() -> None:
    names: list[str] = []
    for component in CLI_COMPONENTS:
        names += [c.name for c in _commands(importlib.import_module(f"orchestra.{component}.cli"))]
    names += [c.name for c in _commands(importlib.import_module(COMPONENT_STATUS_MODULE))]
    duplicated = sorted({name for name in names if names.count(name) > 1})
    assert duplicated == []


def test_name_guard_passes_on_the_real_component_cli_modules() -> None:
    assert _real_violations(NAME_GUARD_FILES, command_name_violations) == {}


def test_name_guard_flags_a_seeded_command_name_set() -> None:
    seeded = 'VERBS = frozenset({"a", "b"})\nOTHER = {"x"}\n'
    assert command_name_violations(seeded) == [
        "command name set at line 1",
        "command name set at line 2",
    ]


def test_name_guard_flags_a_seeded_dispatch_chain() -> None:
    seeded = (
        "def f(args):\n"
        "    if args.command == 'a':\n        return 1\n"
        "    elif args.command == 'b':\n        return 2\n"
    )
    assert command_name_violations(seeded) == ["command dispatch chain at line 2"]


def test_name_guard_flags_a_seeded_local_subparser_protocol() -> None:
    seeded = (
        "from typing import Protocol\n"
        "class SubparserGroup(Protocol):\n    def add_parser(self, name): ...\n"
        "class Other(Protocol):\n    def add_parser(self, name): ...\n"
    )
    assert command_name_violations(seeded) == [
        "local subparser protocol SubparserGroup at line 2",
        "local subparser protocol Other at line 4",
    ]


def test_name_guard_ignores_a_single_command_check_and_plain_sets() -> None:
    clean = (
        "def f(args, names):\n    if args.command == 'a':\n        return 1\n    return 2\n"
        "NAMES = {name for name in ()}\n"
    )
    assert command_name_violations(clean) == []


def test_name_guard_flags_a_seeded_tmp_path_module(tmp_path: Path) -> None:
    module = tmp_path / "cli.py"
    module.write_text('VERBS = {"a"}\n', encoding="utf-8")
    assert command_name_violations(module.read_text(encoding="utf-8")) != []


def test_store_not_ready_guard_passes_on_the_real_component_cli_modules() -> None:
    assert _real_violations(STORE_NOT_READY_FILES, store_not_ready_violations) == {}


def test_store_not_ready_guard_flags_a_seeded_plain_except() -> None:
    seeded = "try:\n    pass\nexcept StoreNotReady as exc:\n    raise\n"
    assert store_not_ready_violations(seeded) == ["except StoreNotReady at line 3"]


def test_store_not_ready_guard_flags_a_seeded_tuple_except() -> None:
    seeded = "try:\n    pass\nexcept (ValueError, workspace.StoreNotReady):\n    raise\n"
    assert store_not_ready_violations(seeded) == ["except StoreNotReady at line 3"]


def test_store_not_ready_guard_ignores_other_handlers() -> None:
    seeded = "try:\n    pass\nexcept (ValueError, KeyError):\n    raise\n"
    assert store_not_ready_violations(seeded) == []


def test_store_not_ready_guard_exempts_hooks_and_the_canon_program() -> None:
    assert STORE_NOT_READY_ALLOWED.isdisjoint(STORE_NOT_READY_FILES)
    for path in STORE_NOT_READY_ALLOWED:
        assert (REPO_ROOT / path).is_file(), path
