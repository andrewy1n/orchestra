import io
import json
from pathlib import Path

import pytest

from orchestra import cli
from orchestra.canon.project import Project

REFERENCE_ERROR = "invalid reference: ghost-effort"
NEW_ERROR = "invalid reference: another-ghost"
FORMATS = ("--claude", "--cursor")


def hook_input(fmt: str, root: Path, session: str = "s1", **extra: object) -> dict[str, object]:
    if fmt == "--claude":
        return {"cwd": str(root), "session_id": session, **extra}
    return {
        "workspace_roots": [str(root)],
        "conversation_id": session,
        "status": "completed",
        "loop_count": 0,
        **extra,
    }


def run_hook(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    command: str,
    fmt: str,
    stdin: dict[str, object],
) -> tuple[int, dict[str, object] | None]:
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(stdin)))
    code = cli.main([command, fmt])
    out = capsys.readouterr().out
    if not out.strip():
        return code, None
    parsed: object = json.loads(out)
    assert isinstance(parsed, dict)
    return code, parsed


def set_store_errors(monkeypatch: pytest.MonkeyPatch, errors: list[str]) -> None:
    monkeypatch.setattr(Project, "validate", lambda _project: list(errors))
