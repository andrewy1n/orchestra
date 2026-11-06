import ast
import subprocess
from pathlib import Path

from canon_support import make_project, seed_effort

from orchestra.canon.backend import open_backend
from orchestra.stage import hooks


def test_session_start_backs_up_in_process(tmp_path, monkeypatch):
    monkeypatch.setenv("ORCHESTRA_BASELINE_DIR", str(tmp_path / "baselines"))
    monkeypatch.delenv("CANON_STORE", raising=False)
    project = make_project(tmp_path / "repo")
    seed_effort(project, "alpha")

    canon_calls: list[object] = []
    real_run = subprocess.run

    def spy_run(args: object, *rest: object, **kwargs: object):
        if isinstance(args, (list, tuple)) and args and args[0] == "canon":
            canon_calls.append(args)
        return real_run(args, *rest, **kwargs)  # pyright: ignore[reportCallIssue,reportArgumentType]

    monkeypatch.setattr(subprocess, "run", spy_run)
    backups = project.store_path / "backups"
    before = set(backups.glob("*.db")) if backups.is_dir() else set()

    out = hooks.cmd_start(hooks.CLAUDE, {"cwd": str(project.project_root), "session_id": "s1"})

    assert out is not None
    assert "session-start failed" not in str(out)
    created = set(backups.glob("*.db")) - before
    assert len(created) == 1
    assert canon_calls == []
    assert not open_backend(project.store_path).backup_due(hooks.timedelta(hours=24))


def test_hooks_module_has_no_subprocess_import():
    source = Path(hooks.__file__).read_text()
    imported: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "subprocess" not in imported
