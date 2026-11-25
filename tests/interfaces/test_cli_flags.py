"""Pin the flags accepted by every `orchestra` and `canon` subcommand."""

from __future__ import annotations

import contextlib
import io
import re

import pytest

from interfaces.interfaces_support import ENTRY_POINTS

ORCHESTRA_FLAGS: dict[str, tuple[str, ...]] = {
    "": (),
    "handoff": ("--effort",),
    "view": ("--effort",),
    "brief": (),
    "hook-start": ("--claude", "--cursor"),
    "hook-stop": ("--claude", "--cursor"),
    "status": ("--count",),
    "metrics": (),
    "metrics phases": ("--effort", "--json"),
    "metrics repairs": ("--since",),
    "metrics compare": ("--json",),
    "plugins": (),
    "plugins list": ("--format", "--scope"),
    "workflow": (),
    "workflow preview": ("--cwd", "--json", "--store"),
    "workflow start": ("--cwd", "--json", "--snapshot-token", "--store"),
    "workflow status": ("--cwd", "--json", "--store"),
    "workflow next": ("--cwd", "--json", "--no-brief", "--store"),
    "workflow brief": ("--cwd", "--json", "--skill", "--store"),
    "workflow review": ("--artifact", "--authority", "--basis", "--cwd", "--json", "--store"),
    "workflow amend-check": (
        "--basis",
        "--cwd",
        "--equivalent-command",
        "--expected-revision",
        "--json",
        "--routine-check",
        "--store",
    ),
    "verify": (),
    "verify verdict": ("--at", "--base", "--cwd", "--provenance", "--require-trail"),
    "verify runner-template": (),
    "verify attest": (),
    "verify attest emit": ("--input", "--key"),
    "verify attest verify": ("--allowlist", "--commit", "--input", "--manifest-hash"),
    "verify lint": (),
    "verify lint no-assert": (),
    "verify lint new-skips": ("--base", "--cwd", "--head"),
    "verify lint claims": ("--cwd",),
    "verify claim": (),
    "verify claim add": ("--cwd", "--id", "--test", "--text"),
    "verify freeze": ("--cwd",),
    "verify audit": (
        "--base",
        "--cwd",
        "--head",
        "--max-mutants",
        "--mutants",
        "--probes",
        "--require-trail",
        "--test",
    ),
    "verify trail": ("--claim", "--cwd", "--technique"),
    "verify bind": ("--base", "--claim", "--cwd", "--head", "--observation"),
    "verify unbind": ("--cwd", "--id"),
    "verify recheck": ("--claim", "--cwd"),
    "verify assertion-red": (),
    "check": (
        "--acceptance",
        "--allow-dirty",
        "--cwd",
        "--execution-report",
        "--phase",
        "--standing-constraint",
        "--store",
        "--timeout",
    ),
    "close-batch": ("--cwd", "--input", "--out", "--store"),
    "install": (
        "--all",
        "--copy",
        "--dry-run",
        "--global",
        "--home",
        "--interactive",
        "--list",
        "--non-interactive",
        "--only",
        "--scope",
        "--uninstall",
        "--yes",
        "-l",
        "-y",
    ),
    "sessions": (),
    "sessions report": ("--records",),
    "sessions aggregate": (),
    "review-brief": ("--base", "--cwd", "--out", "--phase", "--phase-head", "--store"),
    "effort": (),
    "effort autonomy": ("--apply", "--cwd", "--json", "--migrate", "--store"),
    "wave": (),
    "wave start": ("--cwd", "--json", "--store"),
    "wave end": ("--cwd", "--json", "--store"),
    "wave resolve": ("--cwd", "--json", "--store"),
    "task": (),
    "task redispatch": ("--cwd", "--expected-revision", "--json", "--store"),
    "task land": ("--cwd", "--evidence", "--json", "--schema", "--store"),
    "analyze": ("--cwd", "--json", "--stage", "--store"),
    "gate": ("--cwd", "--json", "--store"),
    "suite": (),
    "suite policy": ("--cwd",),
    "suite start": (
        "--allow-dirty",
        "--command",
        "--cwd",
        "--phase",
        "--phase-head",
        "--session",
        "--timeout",
    ),
    "suite poll": ("--allow-dirty", "--cwd", "--phase", "--phase-head", "--run-id", "--session"),
    "suite collect": ("--allow-dirty", "--cwd", "--phase", "--phase-head", "--run-id", "--session"),
    "suite record": (
        "--allow-dirty",
        "--criterion-id",
        "--cwd",
        "--effort",
        "--phase",
        "--phase-head",
        "--run-id",
        "--session",
        "--store",
    ),
    "suite cancel": ("--allow-dirty", "--cwd", "--phase", "--phase-head", "--run-id", "--session"),
    "land": ("--base", "--cwd", "--phase", "--poll-interval", "--remote", "--store", "--timeout"),
    "merge-evidence": ("--cwd", "--phase", "--store"),
    "close": ("--all", "--cwd", "--phase", "--store"),
    "store": (),
    "store path": ("--cwd", "--json"),
    "store scan": ("--cwd", "--json"),
    "store recover-evidence": ("--apply", "--cwd"),
    "store run": ("--cwd",),
    "store ensure": ("--cwd", "--json"),
    "idea": ("--area", "--body-file", "--effort", "--source"),
    "place": (),
    "verify plugins": ("--cwd", "--key", "--review-output", "--revision", "--stage", "--test"),
}

CANON_FLAGS: dict[str, tuple[str, ...]] = {
    "": ("--read-only", "--root", "--store"),
    "init": ("--schemas",),
    "create": (
        "--body",
        "--body-file",
        "--payload",
        "--payload-file",
        "--set",
        "--subject",
        "--type",
        "-p",
    ),
    "update": (
        "--body",
        "--body-file",
        "--expected-revision",
        "--id",
        "--payload",
        "--payload-file",
        "--set",
        "--subject",
        "--transition",
        "--type",
        "-p",
    ),
    "supersede": (
        "--body",
        "--body-file",
        "--expected-revision",
        "--id",
        "--payload",
        "--payload-file",
        "--set",
        "--subject",
        "--type",
        "-p",
    ),
    "correct": (
        "--body",
        "--body-file",
        "--expected-revision",
        "--id",
        "--payload",
        "--payload-file",
        "--set",
        "--subject",
        "--type",
        "-p",
    ),
    "apply": ("--file",),
    "get": ("--body-only", "--field", "--id", "--type"),
    "list": (
        "--desc",
        "--exact-subject",
        "--fields",
        "--format",
        "--full",
        "--grep",
        "--has-inbound",
        "--limit",
        "--order-by",
        "--since",
        "--state",
        "--subject",
        "--type",
        "--until",
        "--where",
    ),
    "validate": ("--format",),
    "backup": ("--keep",),
    "export": ("--out", "--store"),
    "import": ("--store",),
    "schemas": (),
    "schemas sync": (),
    "schemas add": (),
    "schemas show": ("--type",),
    "merge": ("--format", "--namespace", "--rename-subject"),
}

HIDDEN_ORCHESTRA_PATHS = ("verify plugins",)

GROUP_PREFIXES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("conductor_suite_gate", ("suite", "gate", "analyze", "review-brief")),
    ("conductor_wave_task", ("wave", "task")),
    ("conductor_land_close", ("land", "close", "close-batch", "merge-evidence")),
    ("conductor_workflow", ("workflow",)),
    ("views", ("handoff", "view", "brief", "status")),
    (
        "light_components",
        (
            "hook-start",
            "hook-stop",
            "metrics",
            "effort",
            "idea",
            "place",
        ),
    ),
)

_SUBCOMMANDS = re.compile(r"^  \{([^}\s]+)\}\n    (\S+)", re.MULTILINE)
_OPTION_LINE = re.compile(r"^  (-.*)$", re.MULTILINE)
_OPTION_NAME = re.compile(r"(?<![\w-])--?[A-Za-z][\w-]*")


def group_of(tool: str, path: str) -> str:
    if tool == "canon":
        return "tuner_canon_stage"
    head = path.split(" ")[0]
    for group, prefixes in GROUP_PREFIXES:
        if head in prefixes:
            return group
    return "tuner_canon_stage"


def help_text(tool: str, path: str) -> str:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), pytest.raises(SystemExit) as stop:
        ENTRY_POINTS[tool]([*path.split(), "--help"])
    assert stop.value.code == 0
    return out.getvalue()


def accepted_flags(text: str) -> tuple[str, ...]:
    names = {
        name
        for line in _OPTION_LINE.findall(text)
        for name in _OPTION_NAME.findall(re.split(r"\s{2,}", line)[0])
    }
    return tuple(sorted(names - {"-h", "--help"}))


def walk(tool: str, path: str = "") -> dict[str, tuple[str, ...]]:
    text = help_text(tool, path)
    found = {path: accepted_flags(text)}
    listing = _SUBCOMMANDS.search(text)
    if listing:
        for name in listing.group(1).split(","):
            found.update(walk(tool, f"{path} {name}".strip()))
    return found


def _params() -> list[object]:
    params: list[object] = []
    for tool, table in (("orchestra", ORCHESTRA_FLAGS), ("canon", CANON_FLAGS)):
        for path, flags in table.items():
            slug = "_".join([tool, *path.split()]).replace("-", "_")
            params.append(pytest.param(tool, path, flags, id=f"{group_of(tool, path)}-{slug}"))
    return params


@pytest.mark.parametrize(("tool", "path", "flags"), _params())
def test_subcommand_accepts_recorded_flags(tool: str, path: str, flags: tuple[str, ...]) -> None:
    assert accepted_flags(help_text(tool, path)) == tuple(sorted(flags))


def test_orchestra_walk_finds_exactly_the_recorded_subcommands() -> None:
    found = walk("orchestra")
    for hidden in HIDDEN_ORCHESTRA_PATHS:
        found[hidden] = accepted_flags(help_text("orchestra", hidden))
    assert found == {path: tuple(sorted(flags)) for path, flags in ORCHESTRA_FLAGS.items()}


def test_canon_walk_finds_exactly_the_recorded_subcommands() -> None:
    found = walk("canon")
    assert found == {path: tuple(sorted(flags)) for path, flags in CANON_FLAGS.items()}
