"""Store client uses Project and does not spawn the artifact CLI (R1–R5)."""

from __future__ import annotations

import ast
import importlib
import pkgutil
import subprocess
from pathlib import Path

import affidavit
import affidavit.binding as binding
import affidavit.observation as observation

OBS_TYPE = "aff:evidence-observation"
BIND_TYPE = "aff:evidence-binding"
_CLI_NAME = "canon"
_PROCESS_FUNCS = frozenset(
    {
        "run",
        "Popen",
        "check_call",
        "check_output",
        "call",
        "system",
        "popen",
        "execv",
        "execvp",
        "execl",
        "execve",
    }
)


def _usable_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    artifacts = root / ".artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "config.json").write_text("{}\n", encoding="utf-8")
    return root


def _block_cli(monkeypatch, *modules: object) -> None:
    def _missing(_name: str) -> None:
        return None

    for module in modules:
        shutil_mod = getattr(module, "shutil", None)
        if shutil_mod is not None:
            monkeypatch.setattr(shutil_mod, "which", _missing)


def _install_project_spy(monkeypatch):
    creates: list[dict] = []
    lists: list[object] = []

    def spy_create(self, *args, **kwargs):
        payload = kwargs.get("payload")
        record = {
            "id": "rec-spy",
            "record_type": kwargs.get("record_type"),
            "subject": kwargs.get("subject"),
            "payload": dict(payload) if isinstance(payload, dict) else {},
        }
        creates.append(record)
        return dict(record)

    def spy_list(self, record_type=None, *args, **kwargs):
        if record_type is None:
            record_type = kwargs.get("record_type")
        lists.append(record_type)
        if record_type == OBS_TYPE:
            return [
                {
                    "id": "rec-obs-marker",
                    "record_type": OBS_TYPE,
                    "payload": {
                        "technique": "verdict",
                        "base_rev": "base-pin",
                        "head_rev": "head-pin",
                        "result": "pass",
                        "claim_ids": ["claim-widget"],
                    },
                }
            ]
        if record_type == BIND_TYPE:
            return [
                {
                    "id": "rec-bind-marker",
                    "record_type": BIND_TYPE,
                    "payload": {
                        "observation_id": "rec-obs-1",
                        "claim_id": "claim-widget",
                        "base_rev": "base-pin",
                        "head_rev": "head-pin",
                    },
                }
            ]
        return []

    try:
        project_mod = importlib.import_module("canon.project")
    except ImportError:
        project_mod = None
    if project_mod is not None:
        monkeypatch.setattr(project_mod.Project, "create", spy_create)
        monkeypatch.setattr(project_mod.Project, "list", spy_list)
    return creates, lists


def _call(fn):
    try:
        return fn(), None
    except AssertionError:
        raise
    except Exception as exc:
        return None, exc


def _payload_matches(record: dict, expected: dict) -> bool:
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return False
    return all(payload.get(key) == value for key, value in expected.items())


def test_store_client_create_observation(tmp_path: Path, monkeypatch) -> None:
    """R1: affidavit.observation creates an evidence-observation by calling Project.create."""
    root = _usable_root(tmp_path)
    creates, _lists = _install_project_spy(monkeypatch)
    _block_cli(monkeypatch, observation)
    result, error = _call(
        lambda: observation.record_observation(
            root,
            technique="verdict",
            base_rev="base-pin",
            head_rev="head-pin",
            result="pass",
            claim_ids=["claim-widget"],
        )
    )
    matched = [
        record
        for record in creates
        if record.get("record_type") == OBS_TYPE
        and _payload_matches(
            record,
            {
                "technique": "verdict",
                "base_rev": "base-pin",
                "head_rev": "head-pin",
                "result": "pass",
            },
        )
    ]
    assert matched, (
        "affidavit.observation creates an evidence-observation by calling Project.create"
    )
    assert error is None
    assert isinstance(result, dict)
    assert result.get("record_type") == OBS_TYPE


def test_store_client_list_observations(tmp_path: Path, monkeypatch) -> None:
    """R2: affidavit.observation lists evidence-observations by calling Project.list."""
    root = _usable_root(tmp_path)
    _creates, lists = _install_project_spy(monkeypatch)
    _block_cli(monkeypatch, observation)
    result, error = _call(lambda: observation.list_observations(root))
    assert OBS_TYPE in lists, (
        "affidavit.observation lists evidence-observations by calling Project.list"
    )
    assert error is None
    assert isinstance(result, list)
    assert any(
        isinstance(item, dict) and item.get("id") == "rec-obs-marker" for item in result
    )


def test_store_client_create_binding(tmp_path: Path, monkeypatch) -> None:
    """R3: affidavit.binding creates an evidence-binding by calling Project.create."""
    root = _usable_root(tmp_path)
    creates, _lists = _install_project_spy(monkeypatch)
    _block_cli(monkeypatch, binding, observation)
    expected = {
        "observation_id": "rec-obs-1",
        "claim_id": "claim-widget",
        "base_rev": "base-pin",
        "head_rev": "head-pin",
    }
    result, error = _call(
        lambda: binding.bind_observation(
            root,
            observation_id="rec-obs-1",
            claim_id="claim-widget",
            base_rev="base-pin",
            head_rev="head-pin",
        )
    )
    matched = [
        record
        for record in creates
        if record.get("record_type") == BIND_TYPE and _payload_matches(record, expected)
    ]
    assert matched, (
        "affidavit.binding creates an evidence-binding by calling Project.create"
    )
    assert error is None
    assert isinstance(result, dict)
    assert _payload_matches(result, expected)


def test_store_client_list_bindings(tmp_path: Path, monkeypatch) -> None:
    """R4: affidavit.binding lists evidence-bindings by calling Project.list."""
    root = _usable_root(tmp_path)
    _creates, lists = _install_project_spy(monkeypatch)
    _block_cli(monkeypatch, binding, observation)
    result, error = _call(lambda: binding.list_bindings(root))
    assert BIND_TYPE in lists, (
        "affidavit.binding lists evidence-bindings by calling Project.list"
    )
    assert error is None
    assert isinstance(result, list)
    assert any(
        isinstance(item, dict) and item.get("id") == "rec-bind-marker" for item in result
    )


def _folded_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _folded_string(node.left)
        right = _folded_string(node.right)
        if left is None or right is None:
            return None
        return left + right
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                return None
        return "".join(parts)
    return None


def _starts_process(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else None
        if name is None and isinstance(func, ast.Name):
            name = func.id
        if name in _PROCESS_FUNCS:
            return True
    return False


def _docstrings(tree: ast.AST) -> set[ast.AST]:
    found: set[ast.AST] = set()

    def consider(body: list[ast.stmt]) -> None:
        if not body or not isinstance(body[0], ast.Expr):
            return
        value = body[0].value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            found.add(value)

    if isinstance(tree, ast.Module):
        consider(tree.body)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            consider(node.body)
    return found


def _names_cli(tree: ast.AST) -> bool:
    docs = _docstrings(tree)
    for node in ast.walk(tree):
        if node in docs:
            continue
        text = _folded_string(node)
        if text is not None and _CLI_NAME in text:
            return True
    return False


def _modules_that_spawn_cli() -> list[str]:
    offenders: list[str] = []
    root = Path(affidavit.__file__).resolve().parent
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if _names_cli(tree) and _starts_process(tree):
            offenders.append(str(path.relative_to(root.parent)))
    return offenders


def _is_aa_command(argv: list[str]) -> bool:
    if any(Path(part).name == _CLI_NAME for part in argv):
        return True
    if "-m" in argv and any(
        part == "canon" or part.startswith("canon.")
        for part in argv
    ):
        return True
    return False


def _note_argv(spawned: list[list[str]], argv) -> None:
    if isinstance(argv, (bytes, bytearray)):
        spawned.append([bytes(argv).decode()])
        return
    if isinstance(argv, str):
        spawned.append([argv])
        return
    try:
        spawned.append([str(part) for part in argv])
    except TypeError:
        spawned.append([str(argv)])


def test_store_client_no_canon_process(tmp_path: Path, monkeypatch) -> None:
    """R5: no module under affidavit/ starts a process to run canon."""
    static = _modules_that_spawn_cli()
    spawned: list[list[str]] = []

    def spy_run(argv, *args, **kwargs):
        _note_argv(spawned, argv)
        return subprocess.CompletedProcess(
            argv,
            0,
            stdout='{"record": {"id": "rec-1", "payload": {}}, "records": []}',
            stderr="",
        )

    modules = [
        importlib.import_module(f"affidavit.{info.name}")
        for info in pkgutil.iter_modules(affidavit.__path__)
    ]
    monkeypatch.setattr(subprocess, "run", spy_run)
    for module in modules:
        sub = getattr(module, "subprocess", None)
        if sub is not None and hasattr(sub, "run"):
            monkeypatch.setattr(sub, "run", spy_run, raising=False)

    root = _usable_root(tmp_path)

    def exercise() -> None:
        observation.record_observation(
            root,
            technique="verdict",
            base_rev="base-pin",
            head_rev="head-pin",
            result="pass",
        )
        observation.list_observations(root)
        binding.bind_observation(
            root,
            observation_id="rec-obs-1",
            claim_id="claim-widget",
            base_rev="base-pin",
            head_rev="head-pin",
        )
        binding.list_bindings(root)

    try:
        exercise()
    except AssertionError:
        raise
    except Exception:
        pass
    spawned_cli = [argv for argv in spawned if _is_aa_command(argv)]
    assert spawned_cli == [], spawned_cli
    assert static == [], static
