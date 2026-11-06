from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_lint_config.py"

_BASE_CONFIG = """\
[tool.basedpyright]
typeCheckingMode = "standard"
include = ["orchestra", "tests"]
strict = ["orchestra"]
reportExplicitAny = "error"
reportIgnoreCommentWithoutRule = "error"

[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I"]
ignore = ["E501"]
"""


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _repo(tmp_path: Path, baseline: bool = False) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "pyproject.toml").write_text(_BASE_CONFIG, encoding="utf-8")
    (tmp_path / "sample.py").write_text("value = 1\n", encoding="utf-8")
    if baseline:
        baseline_path = tmp_path / ".basedpyright" / "baseline.json"
        baseline_path.parent.mkdir()
        baseline_path.write_text("{}\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def _config(root: Path) -> str:
    return (root / "pyproject.toml").read_text(encoding="utf-8")


def _check(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--base", "HEAD", "--root", str(root)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def _replace(root: Path, before: str, after: str) -> None:
    (root / "pyproject.toml").write_text(_config(root).replace(before, after), encoding="utf-8")


def test_equal_policy_passes(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    assert _check(root).returncode == 0


def test_weaker_basedpyright_mode_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _replace(root, 'typeCheckingMode = "standard"', 'typeCheckingMode = "basic"')

    result = _check(root)

    assert result.returncode == 1
    assert "typeCheckingMode is weaker" in result.stdout


def test_removing_strict_path_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _replace(root, 'strict = ["orchestra"]', "strict = []")

    result = _check(root)

    assert result.returncode == 1
    assert "strict removes protected paths" in result.stdout


def test_weaker_ruff_selection_and_ignore_fail(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _replace(root, 'select = ["E", "F", "I"]', 'select = ["E", "F"]')
    _replace(root, 'ignore = ["E501"]', 'ignore = ["E501", "F401"]')

    result = _check(root)

    assert result.returncode == 1
    assert "removes selected rules" in result.stdout
    assert "adds ignored rules" in result.stdout


def test_tighter_policy_passes(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _replace(root, 'typeCheckingMode = "standard"', 'typeCheckingMode = "strict"')
    _replace(root, 'select = ["E", "F", "I"]', 'select = ["E", "F", "I", "B"]')
    _replace(root, 'ignore = ["E501"]', "ignore = []")
    _replace(root, "line-length = 100", "line-length = 88")

    assert _check(root).returncode == 0


def test_new_report_warning_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _replace(
        root,
        'reportExplicitAny = "error"',
        'reportExplicitAny = "error"\nreportUnusedImport = "warning"',
    )

    result = _check(root)

    assert result.returncode == 1
    assert "reportUnusedImport is weaker than the default" in result.stdout


def test_new_report_error_passes(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _replace(
        root,
        'reportExplicitAny = "error"',
        'reportExplicitAny = "error"\nreportUnusedImport = "error"',
    )

    assert _check(root).returncode == 0


def test_unruled_pyright_ignore_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "sample.py").write_text("value = missing  # pyright: ign" + "ore\n", encoding="utf-8")

    result = _check(root)

    assert result.returncode == 1
    assert "unruled pyright ignore" in result.stdout


def test_added_basedpyright_baseline_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    baseline = root / ".basedpyright" / "baseline.json"
    baseline.parent.mkdir()
    baseline.write_text("{}\n", encoding="utf-8")

    result = _check(root)

    assert result.returncode == 1
    assert "baseline.json is not allowed" in result.stdout


def test_existing_basedpyright_baseline_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, baseline=True)

    result = _check(root)

    assert result.returncode == 1
    assert "baseline.json is not allowed" in result.stdout
