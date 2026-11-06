"""External programs run through CliTool; only orchestra/tools imports subprocess."""

from __future__ import annotations

import ast
from collections.abc import Collection, Mapping
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("orchestra", "installer", "dashboard", "scripts")
EXCLUDED_PARTS = ("node_modules",)
EXCLUDED_PREFIXES = ("orchestra/tools/",)
ALLOWLIST: dict[str, str] = {
    "installer/runner.py": "installer runs before orchestra is installed",
    "installer/adapters/tail.py": "installer runs before orchestra is installed",
    "scripts/check_lint_config.py": "CI script run with bare python3",
    "scripts/wheel_smoke.py": "CI script run with bare python3",
    "dashboard/frontend/e2e/serve.py": "starts a long-lived Popen server",
}


def validate_allowlist(mapping: Mapping[str, str]) -> None:
    empty = sorted(path for path, reason in mapping.items() if not reason.strip())
    if empty:
        raise ValueError(f"allowlist entries without a reason: {', '.join(empty)}")


def _imports_subprocess(path: Path) -> bool:
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == "subprocess" for alias in node.names):
                return True
        elif (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module
            and node.module.split(".")[0] == "subprocess"
        ):
            return True
    return False


def subprocess_importers(repo_root: Path) -> frozenset[str]:
    found: set[str] = set()
    for name in SCAN_DIRS:
        for path in sorted((repo_root / name).rglob("*.py")):
            rel = path.relative_to(repo_root)
            posix = rel.as_posix()
            if any(part in EXCLUDED_PARTS for part in rel.parts):
                continue
            if posix.startswith(EXCLUDED_PREFIXES):
                continue
            if _imports_subprocess(path):
                found.add(posix)
    return frozenset(found)


def violations(importers: frozenset[str], allowlist: Collection[str]) -> list[str]:
    messages = [
        f"{path}: imports subprocess; call external programs through CliTool"
        for path in sorted(importers - frozenset(allowlist))
    ]
    messages.extend(
        f"{path}: allowlisted but no longer imports subprocess; remove it from ALLOWLIST"
        for path in sorted(frozenset(allowlist) - importers)
    )
    return messages


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_unlisted_importer_fails(tmp_path: Path) -> None:
    _write(tmp_path, "orchestra/stage/runner.py", "import subprocess\n")
    _write(tmp_path, "scripts/ok.py", "import os\n")
    importers = subprocess_importers(tmp_path)
    result = violations(importers, frozenset())
    assert len(result) == 1
    assert "orchestra/stage/runner.py" in result[0]


def test_stale_allowlist_entry_fails(tmp_path: Path) -> None:
    _write(tmp_path, "scripts/gone.py", "import os\n")
    importers = subprocess_importers(tmp_path)
    result = violations(importers, frozenset({"scripts/gone.py"}))
    assert len(result) == 1
    assert "scripts/gone.py" in result[0]


def test_import_forms_are_detected(tmp_path: Path) -> None:
    _write(tmp_path, "scripts/a.py", "import subprocess\n")
    _write(tmp_path, "scripts/b.py", "import subprocess as sp\n")
    _write(tmp_path, "scripts/c.py", "from subprocess import run\n")
    _write(tmp_path, "scripts/d.py", "def f() -> None:\n    import subprocess\n")
    _write(tmp_path, "scripts/e.py", "x = 'import subprocess'\n")
    assert subprocess_importers(tmp_path) == frozenset(
        {"scripts/a.py", "scripts/b.py", "scripts/c.py", "scripts/d.py"}
    )


def test_tools_tests_and_node_modules_are_not_scanned(tmp_path: Path) -> None:
    _write(tmp_path, "orchestra/tools/cli_tool.py", "import subprocess\n")
    _write(tmp_path, "dashboard/node_modules/pkg/x.py", "import subprocess\n")
    _write(tmp_path, "tests/test_x.py", "import subprocess\n")
    assert subprocess_importers(tmp_path) == frozenset()


def test_syntax_error_surfaces(tmp_path: Path) -> None:
    _write(tmp_path, "scripts/bad.py", "def (\n")
    try:
        subprocess_importers(tmp_path)
    except SyntaxError:
        return
    raise AssertionError("syntax error was swallowed")


def test_real_tree_matches_allowlist() -> None:
    assert violations(subprocess_importers(REPO_ROOT), ALLOWLIST) == []


def test_git_modules_not_allowlisted() -> None:
    migrated = {
        "orchestra/canon/git_backend.py",
        "orchestra/conductor/gate.py",
        "orchestra/conductor/close_batch.py",
        "orchestra/tuner/manifest.py",
        "orchestra/tuner/provenance.py",
        "dashboard/backend/landing.py",
    }
    assert migrated.isdisjoint(ALLOWLIST)


def test_allowlist_entries_have_reasons() -> None:
    validate_allowlist(ALLOWLIST)


def test_empty_reason_fails() -> None:
    with pytest.raises(ValueError, match=r"scripts/x\.py"):
        validate_allowlist({"scripts/x.py": "  "})
    with pytest.raises(ValueError, match=r"scripts/y\.py"):
        validate_allowlist({"scripts/y.py": ""})


def test_allowlist_is_exactly_the_five_standalone_files() -> None:
    assert set(ALLOWLIST) == {
        "installer/runner.py",
        "installer/adapters/tail.py",
        "scripts/check_lint_config.py",
        "scripts/wheel_smoke.py",
        "dashboard/frontend/e2e/serve.py",
    }
