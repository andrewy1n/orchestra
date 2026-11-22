from __future__ import annotations

import argparse
import json

import pytest

from orchestra import cli
from orchestra.canon.workspace import Access, open_for_command
from orchestra.stage import cli as stage_cli
from orchestra.tools import command_kit
from orchestra.tools.command_kit import Command, CommandError


def _parser(commands: list[Command]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="orchestra")
    command_kit.mount(parser.add_subparsers(dest="command", required=True), commands)
    return parser


def test_mount_binds_handler_and_path_for_nested_children():
    def leaf(args: argparse.Namespace) -> int:
        return 7

    def top(args: argparse.Namespace) -> int:
        return 1

    parser = _parser(
        [
            Command(
                "wave",
                "wave verbs",
                children=(Command("start", "start a wave", handle=leaf),),
            ),
            Command("solo", "solo verb", handle=top),
        ]
    )
    nested = parser.parse_args(["wave", "start"])
    assert nested.handler is leaf
    assert nested.passthrough is False
    assert nested.command_path == ("wave", "start")
    solo = parser.parse_args(["solo"])
    assert solo.handler is top
    assert solo.command_path == ("solo",)


def _add_n(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--n", type=int)


def test_mount_calls_configure_to_add_arguments():
    parser = _parser([Command("solo", "x", configure=_add_n, handle=lambda a: 0)])
    assert parser.parse_args(["solo", "--n", "3"]).n == 3


def test_mount_binds_passthrough_flag():
    parser = _parser([Command("verify", "x", handle=lambda a: 0, passthrough=True)])
    args = parser.parse_args(["verify"])
    assert args.passthrough is True


def test_run_prints_prefixed_line_and_returns_code_for_command_error(capsys):
    def boom(args: argparse.Namespace) -> int:
        raise CommandError("phase: broken", 4)

    parser = _parser([Command("wave", "x", children=(Command("start", "x", handle=boom),))])
    args, extra = parser.parse_known_args(["wave", "start"])
    assert command_kit.run(args, extra) == 4
    assert capsys.readouterr().err == "orchestra wave start: phase: broken\n"


def test_command_error_defaults_to_exit_2():
    assert CommandError("x").exit_code == 2


def test_run_returns_handler_result():
    parser = _parser([Command("solo", "x", handle=lambda a: 9)])
    args, extra = parser.parse_known_args(["solo"])
    assert command_kit.run(args, extra) == 9


def test_run_passes_extra_to_handler_only_for_passthrough():
    seen: list[object] = []

    def plain(args: argparse.Namespace) -> int:
        seen.append(("plain", args))
        return 0

    parser = _parser(
        [
            Command("plain", "x", handle=plain),
            Command("verify", "x", handle=lambda a: 0, passthrough=True),
        ]
    )
    args, extra = parser.parse_known_args(["verify", "--foo", "bar"])
    assert extra == ["--foo", "bar"]
    assert command_kit.run(args, extra) == 0
    assert args.extra == ["--foo", "bar"]


def test_run_passthrough_handler_receives_extra_on_namespace():
    got: list[list[str]] = []

    def handle(args: argparse.Namespace) -> int:
        got.append(list(args.extra))
        return 0

    parser = _parser([Command("verify", "x", handle=handle, passthrough=True)])
    args, extra = parser.parse_known_args(["verify", "--foo"])
    command_kit.run(args, extra)
    assert got == [["--foo"]]


def test_fail_prints_prefixed_line_and_returns_code(capsys):
    parser = _parser([Command("solo", "x", handle=lambda a: 0)])
    args = parser.parse_args(["solo"])
    assert command_kit.fail(args, "nope", 3) == 3
    assert capsys.readouterr().err == "orchestra solo: nope\n"


def test_emit_json_compact_form(capsys):
    command_kit.emit_json({"a": 1, "b": [1, 2]}, compact=True)
    assert capsys.readouterr().out == '{"a":1,"b":[1,2]}\n'


def test_emit_json_pretty_form(capsys):
    command_kit.emit_json({"a": 1})
    out = capsys.readouterr().out
    assert out == json.dumps({"a": 1}, indent=2) + "\n"


def test_root_exits_2_on_extra_arguments_for_non_passthrough_verb(monkeypatch):
    monkeypatch.setattr(
        stage_cli,
        "commands",
        lambda: [Command("ping", "x", handle=lambda a: 0)],
        raising=False,
    )
    with pytest.raises(SystemExit) as exc:
        cli.main(["ping", "--bogus"])
    assert exc.value.code == 2


def test_root_dispatches_on_bound_handler(monkeypatch):
    monkeypatch.setattr(
        stage_cli,
        "commands",
        lambda: [Command("ping", "x", handle=lambda a: 17)],
        raising=False,
    )
    assert cli.main(["ping"]) == 17


def test_root_passthrough_command_accepts_extra_arguments(monkeypatch):
    seen: list[list[str]] = []

    def handle(args: argparse.Namespace) -> int:
        seen.append(list(args.extra))
        return 5

    monkeypatch.setattr(
        stage_cli,
        "commands",
        lambda: [Command("ping", "x", handle=handle, passthrough=True)],
        raising=False,
    )
    assert cli.main(["ping", "--bogus"]) == 5
    assert seen == [["--bogus"]]


def test_open_for_command_raises_command_error_exit_2(tmp_path, monkeypatch):
    monkeypatch.delenv("ORCHESTRA_STORE", raising=False)
    with pytest.raises(CommandError) as exc:
        open_for_command(tmp_path, Access.READ, store=tmp_path / "missing")
    assert exc.value.exit_code == 2
    assert exc.value.message.startswith("store_not_ready:")


def test_open_for_command_raises_command_error_with_refused_exit_4(tmp_path, monkeypatch):
    monkeypatch.delenv("ORCHESTRA_STORE", raising=False)
    with pytest.raises(CommandError) as exc:
        open_for_command(tmp_path, Access.READ, store=tmp_path / "missing", refused_exit=4)
    assert exc.value.exit_code == 4
    assert "store_not_ready:" in exc.value.message
