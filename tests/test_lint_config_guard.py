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


def _check_base(root: Path, base: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--base", base, "--root", str(root)],
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


def test_recommended_and_all_modes_pass(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    for mode in ("recommended", "all"):
        _replace(root, 'typeCheckingMode = "standard"', f'typeCheckingMode = "{mode}"')
        assert _check(root).returncode == 0
        _replace(root, f'typeCheckingMode = "{mode}"', 'typeCheckingMode = "standard"')


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


def test_lower_existing_report_severity_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _replace(root, 'reportExplicitAny = "error"', 'reportExplicitAny = "warning"')

    result = _check(root)

    assert result.returncode == 1
    assert "reportExplicitAny is weaker" in result.stdout


def test_unknown_policy_setting_change_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _replace(root, "line-length = 100", "line-length = 100\npreview = true")

    result = _check(root)

    assert result.returncode == 1
    assert "preview changed without a comparison rule" in result.stdout


def test_adding_exclude_when_base_has_none_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _replace(
        root,
        'include = ["orchestra", "tests"]',
        'include = ["orchestra", "tests"]\nexclude = ["tests"]',
    )

    result = _check(root)

    assert result.returncode == 1
    assert "exclude adds excluded paths" in result.stdout


def test_weaker_per_file_ignores_fail(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _replace(
        root,
        'ignore = ["E501"]',
        'ignore = ["E501"]\nper-file-ignores = { "sample.py" = ["F401"] }',
    )

    result = _check(root)

    assert result.returncode == 1
    assert "per-file-ignores weakens sample.py" in result.stdout


def test_unruled_pyright_ignore_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "sample.py").write_text("value = missing  # pyright: ign" + "ore\n", encoding="utf-8")

    result = _check(root)

    assert result.returncode == 1
    assert "unruled Python suppression" in result.stdout


def test_broad_python_suppressions_fail_in_py_and_pyi(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    noqa = "#" + " noqa"
    pyright_setting = "#" + " pyright: reportUnknownMemberType=" + "false"
    (root / "sample.py").write_text(f"value = missing  {noqa}\n", encoding="utf-8")
    (root / "sample.pyi").write_text(f"value: int  {pyright_setting}\n", encoding="utf-8")

    result = _check(root)

    assert result.returncode == 1
    assert "sample.py:1 has an unruled Python suppression" in result.stdout
    assert "sample.pyi:1 has an unruled Python suppression" in result.stdout


def test_pyright_mode_directives_and_ruff_noqa_fail(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    directives = ["#" + " pyright: basic", "#" + " pyright: off", "#" + " ruff: noqa"]
    (root / "sample.py").write_text("\n".join(directives) + "\n", encoding="utf-8")

    result = _check(root)

    assert result.returncode == 1
    assert result.stdout.count("unruled Python suppression") == 3


def test_rule_specific_suppressions_pass(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "sample.py").write_text(
        "value = missing  # pyright: ignore[reportUndefinedVariable]\nvalue = 1  # noqa: F401\n",
        encoding="utf-8",
    )

    assert _check(root).returncode == 0


def test_override_configs_fail(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "nested").mkdir()
    (root / "nested" / "ruff.toml").write_text("line-length = 150\n", encoding="utf-8")
    (root / "nested" / "pyrightconfig.json").write_text("{}\n", encoding="utf-8")

    result = _check(root)

    assert result.returncode == 1
    assert "nested/ruff.toml can override" in result.stdout
    assert "nested/pyrightconfig.json can override" in result.stdout


def test_nested_pyproject_lint_config_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    nested = root / "nested"
    nested.mkdir()
    (nested / "pyproject.toml").write_text("[tool.ruff]\nline-length = 150\n", encoding="utf-8")

    result = _check(root)

    assert result.returncode == 1
    assert "nested/pyproject.toml defines [tool.ruff] policy" in result.stdout


def test_malformed_root_toml_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "pyproject.toml").write_text("[tool.basedpyright\n", encoding="utf-8")

    result = _check(root)

    assert result.returncode == 1
    assert "cannot parse pyproject.toml" in result.stdout


def test_missing_base_commit_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    result = _check_base(root, "missing")

    assert result.returncode == 1
    assert "cannot read pyproject.toml from missing" in result.stdout


def test_undecodable_python_file_fails_closed(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "sample.py").write_bytes(b"\xff")

    result = _check(root)

    assert result.returncode == 1
    assert "cannot read sample.py" in result.stdout


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


def test_nested_basedpyright_baseline_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    baseline = root / "nested" / ".basedpyright" / "baseline.json"
    baseline.parent.mkdir(parents=True)
    baseline.write_text("{}\n", encoding="utf-8")

    result = _check(root)

    assert result.returncode == 1
    assert "nested/.basedpyright/baseline.json is not allowed" in result.stdout
