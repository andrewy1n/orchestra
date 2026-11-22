"""Show the pinned public-result tests fail on a wrong result and survive an equivalent refactor."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DOUBLE_MODULE = "sensitivity_double"
DOUBLE_SOURCE = """
from __future__ import annotations

import os
from collections.abc import Callable

import pytest

_PATCH = pytest.MonkeyPatch()


def _exit_code(mode: str) -> None:
    import orchestra.score.cli as score_cli

    real = score_cli._autonomy

    def run(args: object) -> int:
        code = real(args)
        if mode == "broken" and code == 0:
            return 1
        return code

    _PATCH.setattr(score_cli, "_autonomy", run)


def _hook_output(mode: str) -> None:
    from orchestra.stage import hooks

    real: Callable[..., str] = hooks._start_context

    def start_context(*args: object, **kwargs: object) -> str:
        ctx = real(*args, **kwargs)
        if mode == "broken":
            return ctx.replace("Goal of alpha", "Goal of omega")
        return ctx

    _PATCH.setattr(hooks, "_start_context", start_context)


def _route_body(mode: str) -> None:
    from dashboard.backend.server import schemas
    from dashboard.backend.server.service import Reader

    real = Reader.areas

    def areas(self: Reader) -> schemas.AreasResponse:
        result = real(self)
        if mode == "broken":
            return schemas.AreasResponse(
                [row.model_copy(update={"title": row.title + "!"}) for row in result.root]
            )
        return schemas.AreasResponse(list(result.root))

    _PATCH.setattr(Reader, "areas", areas)


_DOUBLES = {"exit_code": _exit_code, "hook_output": _hook_output, "route_body": _route_body}


def pytest_configure(config: pytest.Config) -> None:
    _DOUBLES[os.environ["SENSITIVITY_SURFACE"]](os.environ["SENSITIVITY_MODE"])
"""


@dataclass(frozen=True)
class Surface:
    name: str
    test_file: str
    selector: str


SURFACES = [
    Surface(
        "exit_code",
        "tests/interfaces/test_cli_exit_codes.py",
        "light_components-effort_autonomy_success",
    ),
    Surface(
        "hook_output",
        "tests/interfaces/test_hook_output.py",
        "test_hook_start_on_clean_store_emits_protocol_and_handoff",
    ),
    Surface("route_body", "tests/interfaces/test_http_routes.py", "areas"),
]


def _run_pinned(surface: Surface, mode: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    (tmp_path / f"{DOUBLE_MODULE}.py").write_text(DOUBLE_SOURCE, encoding="utf-8")
    env = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(
            [str(tmp_path), str(REPO_ROOT), os.environ.get("PYTHONPATH", "")]
        ),
        "SENSITIVITY_SURFACE": surface.name,
        "SENSITIVITY_MODE": mode,
    }
    argv = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-n0",
        "-p",
        "no:cacheprovider",
        "-p",
        DOUBLE_MODULE,
        surface.test_file,
        "-k",
        surface.selector,
    ]
    return subprocess.run(
        argv,
        cwd=REPO_ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


@pytest.mark.parametrize("surface", SURFACES, ids=[s.name for s in SURFACES])
def test_pinned_tests_fail_when_the_public_result_changes(surface: Surface, tmp_path: Path) -> None:
    done = _run_pinned(surface, "broken", tmp_path)

    assert done.returncode == 1, done.stdout + done.stderr
    assert " failed" in done.stdout, done.stdout


@pytest.mark.parametrize("surface", SURFACES, ids=[s.name for s in SURFACES])
def test_pinned_tests_stay_green_after_an_equivalent_internal_refactor(
    surface: Surface, tmp_path: Path
) -> None:
    done = _run_pinned(surface, "equivalent", tmp_path)

    assert done.returncode == 0, done.stdout + done.stderr
    assert " passed" in done.stdout, done.stdout
    assert "failed" not in done.stdout
