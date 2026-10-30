"""Oracles for the dashboard data layer: one store module, per-view loaders, typed API, generated UI types."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS = REPO_ROOT / "tests"
DASHBOARD = REPO_ROOT / "dashboard"
BACKEND = DASHBOARD / "backend"
UI = DASHBOARD / "frontend"
UI_SRC = UI / "src"
OPENAPI_JSON = UI / "openapi.json"
API_TYPES = UI_SRC / "api-types.ts"
TYPES_TS = UI_SRC / "types.ts"
API_SCHEMA_SCRIPT = REPO_ROOT / "scripts" / "api_schema.py"

EXACT_VERSION = re.compile(r"^\d+\.\d+\.\d+$")
OLD_DASHBOARD_TESTS = (
    "test_dashboard_*.py",
    "test_web_dashboard*.py",
    "test_web_fastapi_writes.py",
    "test_idea_dashboard.py",
    "test_proof_dashboard.py",
)


def dashboard_python_files() -> list[Path]:
    return [
        path
        for path in sorted(DASHBOARD.rglob("*.py"))
        if not {"node_modules", "__pycache__"} & set(path.parts)
    ]


def parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(), filename=str(path))


def relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def defined_functions(path: Path) -> set[str]:
    return {
        node.name
        for node in parse(path).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def committed_schema() -> dict:
    assert OPENAPI_JSON.is_file(), "missing dashboard/frontend/openapi.json"
    return json.loads(OPENAPI_JSON.read_text())


def schema_names() -> list[str]:
    return sorted(committed_schema().get("components", {}).get("schemas", {}))


def test_r1_only_store_py_calls_project_list_or_get():
    store = BACKEND / "store.py"
    assert store.is_file(), "missing dashboard/backend/store.py"
    offenders = []
    for path in dashboard_python_files():
        if path == store:
            continue
        for node in ast.walk(parse(path)):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in {"list", "get"}:
                continue
            if "project" in ast.unparse(node.func.value).lower():
                offenders.append(f"{relative(path)}:{node.lineno}")
    assert not offenders, f"Project.list/get called outside store.py: {offenders}"


def test_r2_no_backend_module_contains_run_call():
    offenders = [
        relative(path)
        for path in sorted(BACKEND.rglob("*.py"))
        if "_run(" in path.read_text()
    ]
    assert not offenders, f"backend modules still contain `_run(`: {offenders}"


def test_r3_no_dashboard_module_imports_http_server():
    offenders = []
    for path in dashboard_python_files():
        for node in ast.walk(parse(path)):
            if isinstance(node, ast.Import):
                hit = any(
                    alias.name == "http.server" or alias.name.startswith("http.server.")
                    for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom):
                hit = node.level == 0 and (node.module or "").split(".")[:2] == ["http", "server"]
            else:
                continue
            if hit:
                offenders.append(f"{relative(path)}:{node.lineno}")
    assert not offenders, f"dashboard modules import http.server: {offenders}"


def test_r4_model_py_does_not_exist():
    assert not (BACKEND / "model.py").exists(), "dashboard/backend/model.py must be removed"


def test_r5_each_loader_lives_in_its_own_module():
    modules = {name: BACKEND / f"{name}.py" for name in ("snapshot", "task", "phase", "journal")}
    missing = [relative(path) for path in modules.values() if not path.is_file()]
    assert not missing, f"missing loader modules: {missing}"

    functions = {name: defined_functions(path) for name, path in modules.items()}
    assert "load_snapshot" in functions["snapshot"], "snapshot.py defines no load_snapshot"
    assert "load_journal" in functions["journal"], "journal.py defines no load_journal"
    for name in ("task", "phase"):
        assert any(fn.startswith("load_") for fn in functions[name]), f"{name}.py defines no load_* function"

    owners: dict[str, list[str]] = {}
    for name, found in functions.items():
        for fn in found:
            if fn.startswith("load_"):
                owners.setdefault(fn, []).append(name)
    shared = {fn: mods for fn, mods in owners.items() if len(mods) > 1}
    assert not shared, f"load_* functions defined in more than one loader module: {shared}"


def test_r6_every_api_response_has_a_pydantic_model(store):
    pytest.importorskip("fastapi")
    sys.path.insert(0, str(REPO_ROOT))
    from orchestra.canon.project import open_store
    from dashboard.backend.server.app import create_app

    document = create_app(open_store(store)).openapi()
    known = set(document.get("components", {}).get("schemas", {}))

    def is_model_ref(schema: dict) -> bool:
        if "$ref" in schema:
            return schema["$ref"].rsplit("/", 1)[-1] in known
        variants = schema.get("anyOf") or schema.get("oneOf")
        if variants:
            non_null = [v for v in variants if v.get("type") != "null"]
            return bool(non_null) and all(is_model_ref(v) for v in non_null)
        return False

    untyped = []
    checked = 0
    for path, methods in document["paths"].items():
        if not path.startswith("/api/"):
            continue
        for method, operation in methods.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            checked += 1
            successes = {code: r for code, r in operation.get("responses", {}).items() if code.startswith("2")}
            if not successes:
                untyped.append(f"{method.upper()} {path}: no 2xx response")
                continue
            for code, response in successes.items():
                schema = response.get("content", {}).get("application/json", {}).get("schema", {})
                if not is_model_ref(schema):
                    untyped.append(f"{method.upper()} {path} {code}: {schema or '{}'}")
    assert checked, "no /api/ operations found in the OpenAPI document"
    assert not untyped, "responses without a Pydantic model:\n" + "\n".join(untyped)


def test_r7_api_types_are_generated_from_the_committed_schema():
    assert OPENAPI_JSON.is_file(), "missing dashboard/frontend/openapi.json"
    assert API_TYPES.is_file(), "missing dashboard/frontend/src/api-types.ts"
    dev = json.loads((UI / "package.json").read_text()).get("devDependencies", {})
    version = dev.get("openapi-typescript")
    assert version is not None, "package.json devDependencies lacks openapi-typescript"
    assert EXACT_VERSION.match(version), f"openapi-typescript must be pinned to an exact x.y.z, got {version!r}"
    names = schema_names()
    assert names, "openapi.json has no components.schemas"
    generated = API_TYPES.read_text()
    absent = [name for name in names if name not in generated]
    assert not absent, f"api-types.ts lacks schemas from openapi.json: {absent}"


def test_r8_sync_check_passes_clean_and_fails_when_stale(tmp_path):
    assert API_SCHEMA_SCRIPT.is_file(), "missing scripts/api_schema.py"
    clean = subprocess.run(
        [sys.executable, "scripts/api_schema.py", "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert clean.returncode == 0, f"--check failed on the clean tree:\n{clean.stdout}{clean.stderr}"

    stale = tmp_path / "openapi.json"
    document = committed_schema()
    document.setdefault("paths", {})["/api/bogus"] = {}
    stale.write_text(json.dumps(document, indent=2) + "\n")
    result = subprocess.run(
        [sys.executable, "scripts/api_schema.py", "--check", "--schema", str(stale)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 1, f"--check exit code {result.returncode} on a stale schema"
    assert "api_schema.py" in result.stdout + result.stderr, "--check output does not name api_schema.py"


def test_r9_ui_imports_api_types_and_types_ts_holds_no_api_shape():
    importers = [
        relative(path)
        for path in sorted(UI_SRC.rglob("*.ts")) + sorted(UI_SRC.rglob("*.svelte"))
        if re.search(r"""from\s+['"][^'"]*api-types(\.ts)?['"]""", path.read_text())
    ]
    assert importers, "no file under dashboard/frontend/src imports from api-types"

    names = schema_names()
    assert names, "openapi.json has no components.schemas"
    if not TYPES_TS.is_file():
        return
    text = TYPES_TS.read_text()
    duplicated = [
        name
        for name in names
        if re.search(rf"\b(?:interface\s+{re.escape(name)}\b|type\s+{re.escape(name)}\s*(?:<[^>]*>)?\s*=)", text)
    ]
    assert not duplicated, f"types.ts still declares API shapes: {duplicated}"


def test_r10_dashboard_tests_live_under_tests_dashboard():
    here = TESTS / "dashboard"
    assert here.is_dir(), "missing tests/dashboard/"
    assert len(list(here.glob("test_*.py"))) >= 6, "tests/dashboard/ holds fewer than 6 test files"
    leftovers = sorted(
        {path.name for pattern in OLD_DASHBOARD_TESTS for path in TESTS.glob(pattern)}
    )
    assert not leftovers, f"dashboard tests still directly under tests/: {leftovers}"
