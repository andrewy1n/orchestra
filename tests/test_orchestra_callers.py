"""Failing oracles for orchestra-callers. Product code still has the old behavior."""

from __future__ import annotations

import ast
import importlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from orchestra.conductor import close_batch

ROOT = Path(__file__).resolve().parents[1]
CANON_ROOT = ROOT / "orchestra" / "canon"
CLAIM_ID = "claim-widget"
_OLD_MODULES = ("orchestra.aa_resolve", "dashboard.artifact_store")
_OLD_NAMES = frozenset({"aa_command", "resolve_aa_command"})
_RESOLUTION_MARKERS = ("SE_WORKFLOW_STORE", "store-binding.json", "store-binding.local.json")
_CLI_NAMES = frozenset({"artifacts.py"})


def _python_files(directory: Path) -> list[Path]:
    """Python modules under directory, including directories reached by symlink."""
    found: list[Path] = []
    seen: set[Path] = set()

    def walk(current: Path) -> None:
        resolved = current.resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        for path in sorted(current.iterdir()):
            if path.name == "__pycache__":
                continue
            if path.is_dir():
                walk(path)
            elif path.suffix == ".py" and path.is_file():
                found.append(path)

    walk(directory)
    return found


def _docstring_ids(tree: ast.AST) -> set[int]:
    ids: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", [])
        if not body or not isinstance(body[0], ast.Expr):
            continue
        value = body[0].value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            ids.add(id(value))
    return ids


def _string_constants(tree: ast.AST) -> list[tuple[int, str]]:
    skip = _docstring_ids(tree)
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            found.append((node.lineno, node.value))
    return found


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else ""
    return ""


def _open_store_bindings(tree: ast.AST) -> tuple[set[str], set[str]]:
    aliases: set[str] = set()
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "orchestra.canon.project":
            for alias in node.names:
                if alias.name == "open_store":
                    aliases.add(alias.asname or alias.name)
                elif alias.name == "*":
                    aliases.add("open_store")
        elif isinstance(node, ast.ImportFrom) and node.module == "canon":
            for alias in node.names:
                if alias.name == "project":
                    modules.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "orchestra.canon.project":
                    modules.add(alias.asname or alias.name)
                elif alias.name == "canon":
                    bound = alias.asname or alias.name
                    modules.add(f"{bound}.project")
    return aliases, modules


def _calls_open_store(tree: ast.AST) -> bool:
    aliases, modules = _open_store_bindings(tree)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in aliases:
            return True
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "open_store"
            and _dotted(func.value) in modules
        ):
            return True
    return False


def _other_store_open(tree: ast.AST) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in _OLD_MODULES or any(
                    alias.name.startswith(f"{mod}.") for mod in _OLD_MODULES
                ):
                    found.append((node.lineno, f"import {alias.name}"))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module in _OLD_MODULES or any(module.startswith(f"{mod}.") for mod in _OLD_MODULES):
                found.append((node.lineno, f"from {module} import"))
            if module == "orchestra":
                for alias in node.names:
                    if alias.name in {"aa", "aa_resolve"}:
                        found.append((node.lineno, f"from orchestra import {alias.name}"))
            if module == "dashboard":
                for alias in node.names:
                    if alias.name == "artifact_store":
                        found.append((node.lineno, "from dashboard import artifact_store"))
        elif isinstance(node, ast.Name) and node.id in _OLD_NAMES:
            found.append((node.lineno, node.id))
        elif isinstance(node, ast.Attribute) and node.attr in _OLD_NAMES:
            found.append((node.lineno, node.attr))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in _OLD_NAMES:
            found.append((node.lineno, f"def {node.name}"))
    for lineno, text in _string_constants(tree):
        if any(marker in text for marker in _RESOLUTION_MARKERS):
            found.append((lineno, "store binding resolution"))
        elif Path(text.strip()).name in _CLI_NAMES:
            found.append((lineno, f"command {Path(text.strip()).name}"))
    return found


def _store_access(directory: Path) -> tuple[list[str], list[str]]:
    offenders: list[str] = []
    callers: list[str] = []
    for path in _python_files(directory):
        if CANON_ROOT in path.parents:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = path.relative_to(ROOT).as_posix()
        if _calls_open_store(tree):
            callers.append(rel)
        for lineno, reason in _other_store_open(tree):
            offenders.append(f"{rel}:{lineno}: {reason}")
    return offenders, callers


def _module(name: str):
    try:
        return importlib.import_module(name)
    except ImportError:
        return None


def _tuner_argv(cmd) -> list[str] | None:
    if isinstance(cmd, bytes):
        argv = os.fsdecode(cmd).split()
    elif isinstance(cmd, str):
        argv = cmd.split()
    else:
        argv = [os.fsdecode(part) if isinstance(part, bytes) else str(part) for part in cmd]
    if argv and Path(argv[0]).name == "aff":
        return argv
    return None


def _patch_tuner(monkeypatch, started: list[list[str]]) -> None:
    real_run = subprocess.run

    def spy(cmd, *args, **kwargs):
        argv = _tuner_argv(cmd)
        if argv is not None:
            started.append(argv)
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", spy)


def _spy(monkeypatch, module_name: str, attr: str, calls: list) -> None:
    module = _module(module_name)

    def wrapped(*args, **kwargs):
        calls.append((args, kwargs))
        return True if attr == "is_assertion_level_red" else {"result": "pass"}

    if module is not None and hasattr(module, attr):
        monkeypatch.setattr(module, attr, wrapped)


def _check_loader(check_run_id: str) -> dict:
    return {
        "id": check_run_id,
        "payload": {
            "criterion_id": "rec-ac1",
            "result": "pass",
            "runner": "orchestra",
            "revision": "abc123",
            "method": "check",
        },
    }


def _claim_acceptance() -> dict:
    return {
        "id": "rec-ac1",
        "subject": CLAIM_ID,
        "payload": {"method": "check", "effort": "effort-1", "claim": CLAIM_ID},
    }


def _write_manifest(repo: Path) -> None:
    directory = repo / ".tuner"
    directory.mkdir(parents=True)
    (directory / "manifest.json").write_text(
        json.dumps(
            {
                "claims": [
                    {
                        "id": CLAIM_ID,
                        "text": "widget works",
                        "tests": ["tests/test_widget.py::test_widget"],
                        "oracle_hashes": {},
                    }
                ],
                "amendments": [],
            }
        ),
        encoding="utf-8",
    )


def _claim_request() -> dict:
    return {
        "subject": "task-1",
        "effort": "effort-1",
        "work_item_id": "rec-wi",
        "transition": "done",
        "acceptance_ids": ["rec-ac1"],
        "criteria": [
            {
                "criterion_id": "rec-ac1",
                "method": "check",
                "check_run_id": "rec-green",
                "result": "pass",
            }
        ],
    }


def _run_claim_close(repo: Path):
    try:
        close_batch.build_batch(
            _claim_request(),
            cwd=repo,
            load_check_run=_check_loader,
            load_acceptance=lambda _acceptance_id: _claim_acceptance(),
        )
    except Exception as exc:
        return exc
    return None


def _oracle_request() -> dict:
    digest = "ab" * 32
    return {
        "subject": "task-1",
        "effort": "effort-1",
        "work_item_id": "rec-wi",
        "transition": "done",
        "acceptance_ids": ["rec-ac1"],
        "criteria": [
            {
                "criterion_id": "rec-ac1",
                "method": "tdd",
                "check_run_id": "rec-green",
                "result": "pass",
                "revision": "deadbeef",
                "red_check_run_id": "rec-red",
                "red_result": "fail",
                "red_revision": "dirty",
                "red_diff_sha256": "a" * 64,
            }
        ],
    }, {
        "id": "rec-ac1",
        "payload": {
            "method": "tdd",
            "effort": "effort-1",
            "test_ids": ["tests/test_oracle_probe.py::test_expected_behavior"],
            "oracle_hashes": f"tests/test_oracle_probe.py:sha256:{digest}",
        },
    }


def _oracle_loader(check_run_id: str) -> dict:
    if check_run_id == "rec-green":
        return {
            "id": check_run_id,
            "payload": {
                "criterion_id": "rec-ac1",
                "result": "pass",
                "runner": "orchestra",
                "revision": "deadbeef",
                "method": "tdd",
            },
        }
    if check_run_id == "rec-red":
        return {
            "id": check_run_id,
            "body": (
                "E       AssertionError: assert 0 == 42\n"
                "FAILED tests/test_oracle_probe.py::test_expected_behavior - AssertionError\n"
            ),
            "payload": {
                "criterion_id": "rec-ac1",
                "result": "fail",
                "runner": "orchestra",
                "revision": "dirty",
                "method": "tdd",
                "diff_sha256": "a" * 64,
                "failing_node_ids": ["tests/test_oracle_probe.py::test_expected_behavior"],
            },
        }
    raise LookupError(check_run_id)


def _dependency_names(text: str) -> list[str]:
    data = _load_toml(text)
    project = data.get("project") if isinstance(data, dict) else None
    deps = project.get("dependencies") if isinstance(project, dict) else None
    if not isinstance(deps, list):
        return []
    return [_normalize_dep(str(item)) for item in deps]


def _load_toml(text: str) -> dict:
    try:
        import tomllib
    except ModuleNotFoundError:
        tomllib = None
    if tomllib is not None:
        loaded = tomllib.loads(text)
        return loaded if isinstance(loaded, dict) else {}
    try:
        import tomli
    except ModuleNotFoundError:
        return _loose_dependencies(text)
    loaded = tomli.loads(text)
    return loaded if isinstance(loaded, dict) else {}


def _loose_dependencies(text: str) -> dict:
    match = re.search(r"(?ms)^\[project\]\s*(.*?)^\[", text + "\n[")
    body = match.group(1) if match else ""
    dep = re.search(r"(?s)dependencies\s*=\s*\[(.*?)\]", body)
    if not dep:
        return {}
    specs = re.findall(r'"([^"]+)"|\'([^\']+)\'', dep.group(1))
    return {"project": {"dependencies": [left or right for left, right in specs]}}


def _normalize_dep(spec: str) -> str:
    match = re.match(r"\s*([A-Za-z0-9_.-]+)", spec)
    raw = match.group(1) if match else spec
    return raw.replace("_", "-").lower()


def test_r1():
    """R1: modules under orchestra/ open the store with canon.project.open_store."""
    offenders, callers = _store_access(ROOT / "orchestra")
    assert not offenders, "orchestra opens the store another way: " + "; ".join(offenders)
    assert callers, "no orchestra module calls canon.project.open_store"


def test_r2():
    """R2: modules under dashboard/ open the store with canon.project.open_store."""
    offenders, callers = _store_access(ROOT / "dashboard")
    assert not offenders, "dashboard opens the store another way: " + "; ".join(offenders)
    assert callers, "no dashboard module calls canon.project.open_store"


def test_r3():
    """R3: orchestra/aa_resolve.py is not in the tree."""
    path = ROOT / "orchestra" / "aa_resolve.py"
    assert not path.exists(), f"{path.relative_to(ROOT)} is still in the tree"


def test_r4():
    """R4: dashboard/artifact_store.py is not in the tree."""
    path = ROOT / "dashboard" / "artifact_store.py"
    assert not path.exists(), f"{path.relative_to(ROOT)} is still in the tree"


def test_r5(tmp_path, monkeypatch):
    """R5: close_batch calls is_assertion_level_red and does not start aff for that check."""
    calls: list = []
    started: list[list[str]] = []
    _spy(monkeypatch, "orchestra.tuner.oracle_red", "is_assertion_level_red", calls)
    _patch_tuner(monkeypatch, started)
    request, acceptance = _oracle_request()
    try:
        close_batch.build_batch(
            request,
            cwd=tmp_path,
            load_check_run=_oracle_loader,
            load_acceptance=lambda _acceptance_id: acceptance,
            list_oracle_amendments=lambda _acceptance_id: [],
        )
    except Exception:
        pass
    tuner_red = [cmd for cmd in started if "assertion-red" in cmd]
    assert calls, f"close_batch did not call is_assertion_level_red; aff starts={started!r}"
    assert not tuner_red, f"close_batch started aff for assertion-level red: {tuner_red!r}"


def test_r6(tmp_path, monkeypatch):
    """R6: close_batch calls run_verdict for a manifest claim and does not start aff."""
    calls: list = []
    started: list[list[str]] = []
    _spy(monkeypatch, "orchestra.tuner.verdict", "run_verdict", calls)
    _spy(monkeypatch, "orchestra.tuner.binding", "recheck", [])
    _patch_tuner(monkeypatch, started)
    _write_manifest(tmp_path)
    _run_claim_close(tmp_path)
    tuner_verdict = [cmd for cmd in started if "verdict" in cmd]
    assert calls, f"close_batch did not call run_verdict; aff starts={started!r}"
    assert not tuner_verdict, f"close_batch started aff for verdict: {tuner_verdict!r}"


def test_r7(tmp_path, monkeypatch):
    """R7: close_batch calls recheck for a manifest claim and does not start aff."""
    calls: list = []
    started: list[list[str]] = []
    _spy(monkeypatch, "orchestra.tuner.verdict", "run_verdict", [])
    _spy(monkeypatch, "orchestra.tuner.binding", "recheck", calls)
    _patch_tuner(monkeypatch, started)
    _write_manifest(tmp_path)
    _run_claim_close(tmp_path)
    tuner_recheck = [cmd for cmd in started if "recheck" in cmd]
    assert calls, f"close_batch did not call recheck; aff starts={started!r}"
    assert not tuner_recheck, f"close_batch started aff for recheck: {tuner_recheck!r}"


def test_r9(tmp_path, monkeypatch):
    """R9: a claim-backed close names tuner when tuner is not importable."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    aff = bin_dir / "aff"
    aff.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    aff.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")

    saved = {
        key: sys.modules.pop(key)
        for key in list(sys.modules)
        if key == "orchestra.tuner" or key.startswith("orchestra.tuner.")
    }

    class _BlockTuner:
        def find_spec(self, fullname, path, target=None):
            if fullname == "orchestra.tuner" or fullname.startswith("orchestra.tuner."):
                raise ModuleNotFoundError(f"No module named {fullname!r}")
            return None

    blocker = _BlockTuner()
    sys.meta_path.insert(0, blocker)
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_manifest(repo)
    try:
        error = _run_claim_close(repo)
        assert error is not None and "tuner" in str(error).lower(), (
            f"claim-backed close did not name tuner: {error!r}"
        )
    finally:
        if blocker in sys.meta_path:
            sys.meta_path.remove(blocker)
        sys.modules.update(saved)


def test_r10():
    """R10: canon ships inside the orchestra distribution, not as a dependency."""
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    names = _dependency_names(text)
    assert "canon" not in names, f"project.dependencies={names!r}"
    assert '"orchestra.canon"' in text
