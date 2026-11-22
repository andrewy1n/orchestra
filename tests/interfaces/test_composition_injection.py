from __future__ import annotations

import argparse
import ast
import contextlib
import importlib
import io
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

import pytest

from interfaces.test_component_cli_layout import ROOT_CLI_SOURCE, root_composes_violations
from orchestra.canon import cli as canon_cli
from orchestra.views import cli as views_cli

conductor_cli = importlib.import_module("orchestra.conductor.cli")
stage_cli = importlib.import_module("orchestra.stage.cli")


class SubparserGroup(Protocol):
    def add_parser(self, name: str, *, help: str) -> argparse.ArgumentParser: ...


REPO_ROOT = Path(__file__).resolve().parents[2]
SLOT_MODULES = (
    "orchestra/canon/store_commands.py",
    "orchestra/conductor/cli/wave_commands.py",
    "orchestra/stage/cli.py",
    "orchestra/views/cli.py",
)
REMOVED_NAMES = {"install_store_operations", "install_brief_renderer"}
PHASE = "p1"


def _slot_violations(source: str) -> list[str]:
    tree = ast.parse(source)
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
            node.name in REMOVED_NAMES
        ):
            found.append(f"def {node.name}")
        elif isinstance(node, ast.alias) and node.name in REMOVED_NAMES:
            found.append(f"import {node.name}")
        elif isinstance(node, ast.Name) and node.id in REMOVED_NAMES:
            found.append(f"use {node.id}")
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and "not installed" in node.value
        ):
            found.append(f"message {node.value!r}")
    for node in tree.body:
        if not isinstance(node, ast.Assign | ast.AnnAssign):
            continue
        value = node.value
        empty = (isinstance(value, ast.List | ast.Set) and not value.elts) or (
            isinstance(value, ast.Dict) and not value.keys
        )
        if empty:
            found.append("mutable slot")
    return found


@pytest.mark.parametrize("relative", SLOT_MODULES)
def test_no_module_level_install_slot_remains(relative: str) -> None:
    source = (REPO_ROOT / relative).read_text(encoding="utf-8")
    assert _slot_violations(source) == []


def test_slot_checker_flags_a_seeded_registry() -> None:
    seeded = "_ops: list[int] = []\n\ndef install_store_operations(a, b):\n    pass\n"
    assert _slot_violations(seeded) != []


def _canon_adder(sub: SubparserGroup) -> None:
    scan, recover = stage_cli.store_operations()
    canon_cli.add_parsers(sub, scan=scan, recover=recover)


def _conductor_adder(sub: SubparserGroup) -> None:
    conductor_cli.add_parsers(sub, render_brief=views_cli.render_brief)


def _stage_adder(sub: SubparserGroup) -> None:
    stage_cli.add_parsers(sub)


def _views_adder(sub: SubparserGroup) -> None:
    views_cli.add_parsers(sub)


Adder = Callable[[SubparserGroup], None]
ORDERS: dict[str, tuple[Adder, ...]] = {
    "canon-alone": (_canon_adder,),
    "conductor-alone": (_conductor_adder,),
    "reversed": (_conductor_adder, _canon_adder, _views_adder, _stage_adder),
    "forward": (_stage_adder, _views_adder, _canon_adder, _conductor_adder),
}


def _parse(adders: tuple[Adder, ...], argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="orchestra")
    sub = parser.add_subparsers(dest="command", required=True)
    for adder in adders:
        adder(sub)
    return parser.parse_args(argv)


def _run(
    run: Callable[[argparse.Namespace], int], args: argparse.Namespace, cwd: Path
) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    previous = Path.cwd()
    os.chdir(cwd)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = run(args)
    finally:
        os.chdir(previous)
    return code, out.getvalue(), err.getvalue()


def _needed(order: str, verb: str) -> bool:
    return (verb == "wave" and order != "canon-alone") or (
        verb == "store" and order != "conductor-alone"
    )


CASES = [
    (["store", "scan"], canon_cli.run, "store"),
    (["store", "recover-evidence"], canon_cli.run, "store"),
    (["wave", "start", PHASE], conductor_cli.run, "wave"),
]


@pytest.mark.parametrize("order", sorted(ORDERS))
@pytest.mark.parametrize(("argv", "run", "verb"), CASES)
def test_verbs_refuse_without_a_store_in_any_parser_build_order(
    order: str,
    argv: list[str],
    run: Callable[[argparse.Namespace], int],
    verb: str,
    bare_dir: Path,
) -> None:
    if not _needed(order, verb):
        pytest.skip("component not built in this order")
    args = _parse(ORDERS[order], argv)
    code, _, err = _run(run, args, bare_dir)
    assert code == 2
    assert "not installed" not in err


@pytest.mark.parametrize("order", sorted(ORDERS))
def test_store_scan_runs_in_any_parser_build_order(order: str, shared_world: Path) -> None:
    if not _needed(order, "store"):
        pytest.skip("component not built in this order")
    args = _parse(ORDERS[order], ["store", "scan"])
    code, _, err = _run(canon_cli.run, args, shared_world)
    assert code == 0, err


@pytest.mark.parametrize("order", sorted(ORDERS))
def test_store_recover_evidence_runs_in_any_parser_build_order(
    order: str, shared_world: Path
) -> None:
    if not _needed(order, "store"):
        pytest.skip("component not built in this order")
    args = _parse(ORDERS[order], ["store", "recover-evidence"])
    code, _, err = _run(canon_cli.run, args, shared_world)
    assert code == 0, err


@pytest.mark.parametrize("order", sorted(ORDERS))
def test_wave_start_runs_in_any_parser_build_order(order: str, fresh_world: Path) -> None:
    if not _needed(order, "wave"):
        pytest.skip("component not built in this order")
    args = _parse(ORDERS[order], ["wave", "start", PHASE])
    code, out, err = _run(conductor_cli.run, args, fresh_world)
    assert code == 0, err
    assert PHASE in out


def test_parser_built_twice_in_one_process_still_runs_every_verb(
    fresh_world: Path, shared_world: Path
) -> None:
    both = ORDERS["forward"]
    _parse(both, ["store", "scan"])
    scan = _parse(both, ["store", "scan"])
    again = _parse(ORDERS["reversed"], ["wave", "start", PHASE])
    assert _run(canon_cli.run, scan, shared_world)[0] == 0
    assert _run(conductor_cli.run, again, fresh_world)[0] == 0


FRESH_SCRIPT = """
import sys
from orchestra import cli
from orchestra.canon import cli as canon_cli
from orchestra.conductor import cli as conductor_cli

parser = cli._build_parser()
args = parser.parse_args(sys.argv[1:])
run = canon_cli.run if args.command == "store" else conductor_cli.run
sys.exit(run(args))
"""


def _fresh(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", FRESH_SCRIPT, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("argv", [["store", "scan"], ["store", "recover-evidence"]])
def test_store_verbs_run_in_a_fresh_interpreter_through_the_root_parser(
    argv: list[str], shared_world: Path
) -> None:
    done = _fresh(argv, shared_world)
    assert done.returncode == 0, done.stderr
    assert "not installed" not in done.stderr


def test_wave_start_runs_in_a_fresh_interpreter_through_the_root_parser(
    fresh_world: Path,
) -> None:
    done = _fresh(["wave", "start", PHASE], fresh_world)
    assert done.returncode == 0, done.stderr
    assert PHASE in done.stdout


def test_wave_start_refuses_without_a_store_in_a_fresh_interpreter(bare_dir: Path) -> None:
    done = _fresh(["wave", "start", PHASE], bare_dir)
    assert done.returncode == 2
    assert "not installed" not in done.stderr


def test_root_cli_still_only_composes_component_clis() -> None:
    assert root_composes_violations(ROOT_CLI_SOURCE) == []
