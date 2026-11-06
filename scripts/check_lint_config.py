from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

_MODES = {"off": 0, "basic": 1, "standard": 2, "strict": 3, "recommended": 4, "all": 5}
_SEVERITIES = {"none": 0, "off": 0, "information": 1, "warning": 2, "error": 3}
_SUPPRESSIONS = re.compile(
    r"#\s*(?:pyright:\s*(?:ignore(?!\[)|(?:basic|standard|off)\b|report[\w.]+\s*=\s*(?:false|off|none)\b)|(?:ruff:\s*)?noqa(?:\s*:\s*)?(?:\s+#.*)?$)",
    re.IGNORECASE,
)
_SKIP_DIRS = {".git", ".pytest_cache", ".venv", "node_modules", ".worktrees"}


def _nested(value: dict[str, object], *keys: str) -> object | None:
    current: object = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _strings(value: object) -> set[str] | None:
    if not isinstance(value, list):
        return None
    strings: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            return None
        strings.add(item)
    return strings


def _flatten(
    value: dict[str, object], prefix: tuple[str, ...] = ()
) -> dict[tuple[str, ...], object]:
    flattened: dict[tuple[str, ...], object] = {}
    for key, child in value.items():
        path = (*prefix, key)
        if isinstance(child, dict):
            flattened.update(_flatten(child, path))
        else:
            flattened[path] = child
    return flattened


def _compare_sections(base: dict[str, object], candidate: dict[str, object]) -> list[str]:
    failures: list[str] = []
    base_tools = _nested(base, "tool")
    candidate_tools = _nested(candidate, "tool")
    if not isinstance(base_tools, dict) or not isinstance(candidate_tools, dict):
        return ["pyproject.toml must define tool sections in both revisions"]

    base_pyright = base_tools.get("basedpyright")
    candidate_pyright = candidate_tools.get("basedpyright")
    if not isinstance(base_pyright, dict) or not isinstance(candidate_pyright, dict):
        failures.append("[tool.basedpyright] must exist in both revisions")
    else:
        base_mode = base_pyright.get("typeCheckingMode")
        candidate_mode = candidate_pyright.get("typeCheckingMode")
        if isinstance(base_mode, str) and (
            not isinstance(candidate_mode, str)
            or _MODES.get(candidate_mode, -1) < _MODES.get(base_mode, -1)
        ):
            failures.append("[tool.basedpyright].typeCheckingMode is weaker")

        for key in ("strict", "include"):
            before = _strings(base_pyright.get(key))
            after = _strings(candidate_pyright.get(key))
            if before is not None and (after is None or not before <= after):
                failures.append(f"[tool.basedpyright].{key} removes protected paths")

        report_keys = {
            key
            for key in base_pyright.keys() | candidate_pyright.keys()
            if key.startswith("report")
        }
        for key in sorted(report_keys):
            before = base_pyright.get(key)
            after = candidate_pyright.get(key)
            if before is None:
                if after != "error":
                    failures.append(f"[tool.basedpyright].{key} is weaker than the default")
            elif after is None:
                failures.append(f"[tool.basedpyright].{key} was removed")
            elif not isinstance(before, str) or not isinstance(after, str):
                if before != after:
                    failures.append(f"[tool.basedpyright].{key} changed")
            elif _SEVERITIES.get(after, -1) < _SEVERITIES.get(before, -1):
                failures.append(f"[tool.basedpyright].{key} is weaker")

        before_exclude = _strings(base_pyright.get("exclude", []))
        after_exclude = _strings(candidate_pyright.get("exclude", []))
        if before_exclude is None or after_exclude is None:
            failures.append("[tool.basedpyright].exclude must be a string list")
        elif not after_exclude <= before_exclude:
            failures.append("[tool.basedpyright].exclude adds excluded paths")

        known_pyright = {"typeCheckingMode", "strict", "include", "exclude"}
        known_pyright.update(key for key in base_pyright if key.startswith("report"))
        known_pyright.update(key for key in candidate_pyright if key.startswith("report"))
        failures.extend(
            _compare_unknown_fields(
                base_pyright, candidate_pyright, known_pyright, "[tool.basedpyright]"
            )
        )

    base_ruff = base_tools.get("ruff")
    candidate_ruff = candidate_tools.get("ruff")
    if not isinstance(base_ruff, dict) or not isinstance(candidate_ruff, dict):
        failures.append("[tool.ruff] must exist in both revisions")
    else:
        base_lint = base_ruff.get("lint", {})
        candidate_lint = candidate_ruff.get("lint", {})
        if not isinstance(base_lint, dict) or not isinstance(candidate_lint, dict):
            failures.append("[tool.ruff.lint] must be a table")
            base_lint = {}
            candidate_lint = {}

        before_select = (_strings(base_lint.get("select")) or set()) | (
            _strings(base_lint.get("extend-select")) or set()
        )
        after_select = (_strings(candidate_lint.get("select")) or set()) | (
            _strings(candidate_lint.get("extend-select")) or set()
        )
        if not before_select <= after_select:
            failures.append("[tool.ruff.lint] removes selected rules")

        before_ignore = (_strings(base_lint.get("ignore")) or set()) | (
            _strings(base_lint.get("extend-ignore")) or set()
        )
        after_ignore = (_strings(candidate_lint.get("ignore")) or set()) | (
            _strings(candidate_lint.get("extend-ignore")) or set()
        )
        if not after_ignore <= before_ignore:
            failures.append("[tool.ruff.lint] adds ignored rules")

        before_length = base_ruff.get("line-length")
        after_length = candidate_ruff.get("line-length")
        if (
            isinstance(before_length, int)
            and isinstance(after_length, int)
            and after_length > before_length
        ):
            failures.append("[tool.ruff].line-length is longer")

        for key in ("exclude", "extend-exclude"):
            before = _strings(base_ruff.get(key)) or set()
            after = _strings(candidate_ruff.get(key)) or set()
            if not after <= before:
                failures.append(f"[tool.ruff].{key} adds excluded paths")

        before_file_ignores = base_lint.get("per-file-ignores", {})
        after_file_ignores = candidate_lint.get("per-file-ignores", {})
        if isinstance(before_file_ignores, dict) and isinstance(after_file_ignores, dict):
            for pattern, ignored in after_file_ignores.items():
                base_ignored = _strings(before_file_ignores.get(pattern))
                candidate_ignored = _strings(ignored)
                if (
                    base_ignored is None
                    or candidate_ignored is None
                    or not candidate_ignored <= base_ignored
                ):
                    failures.append(f"[tool.ruff.lint].per-file-ignores weakens {pattern}")

        known_ruff = {"line-length", "exclude", "extend-exclude", "lint"}
        failures.extend(
            _compare_unknown_fields(base_ruff, candidate_ruff, known_ruff, "[tool.ruff]")
        )
        known_lint = {"select", "extend-select", "ignore", "extend-ignore", "per-file-ignores"}
        failures.extend(
            _compare_unknown_fields(base_lint, candidate_lint, known_lint, "[tool.ruff.lint]")
        )

    return failures


def _compare_unknown_fields(
    base: dict[str, object],
    candidate: dict[str, object],
    known: set[str],
    label: str,
) -> list[str]:
    failures: list[str] = []
    base_flat = _flatten({key: value for key, value in base.items() if key not in known})
    candidate_flat = _flatten({key: value for key, value in candidate.items() if key not in known})
    for path in sorted(base_flat.keys() | candidate_flat.keys()):
        if base_flat.get(path) != candidate_flat.get(path):
            full_path = ".".join(path)
            failures.append(f"{label}.{full_path} changed without a comparison rule")
    return failures


def _toml(text: str) -> dict[str, object]:
    value = tomllib.loads(text)
    return value


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)


def _files(root: Path) -> list[Path]:
    found: list[Path] = []

    def fail(error: OSError) -> None:
        raise error

    for directory, names, files in os.walk(root, onerror=fail):
        names[:] = sorted(name for name in names if name not in _SKIP_DIRS)
        parent = Path(directory)
        found.extend(parent / name for name in sorted(files))
    return sorted(found)


def _check_override_configs(root: Path, paths: list[Path]) -> list[str]:
    failures: list[str] = []
    for path in paths:
        relative = path.relative_to(root)
        if path.name in {"pyrightconfig.json", "ruff.toml", ".ruff.toml"}:
            failures.append(f"{relative} can override the root Python policy")
        elif path.name == "pyproject.toml" and relative != Path("pyproject.toml"):
            try:
                config = _toml(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                failures.append(f"cannot read nested config {relative}: {exc}")
                continue
            tools = _nested(config, "tool")
            if isinstance(tools, dict):
                for name in ("ruff", "basedpyright"):
                    if name in tools:
                        failures.append(f"{relative} defines [tool.{name}] policy")
    return failures


def check(root: Path, base: str) -> list[str]:
    base_result = _git(root, "show", f"{base}:pyproject.toml")
    if base_result.returncode != 0:
        return [f"cannot read pyproject.toml from {base}: {base_result.stderr.strip()}"]
    try:
        base_config = _toml(base_result.stdout)
        current_config = _toml((root / "pyproject.toml").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"cannot parse pyproject.toml: {exc}"]

    try:
        paths = _files(root)
    except OSError as exc:
        return [f"cannot scan repository files: {exc}"]

    failures = _compare_sections(base_config, current_config)
    failures.extend(_check_override_configs(root, paths))
    for path in paths:
        relative = path.relative_to(root)
        if path.name == "baseline.json" and relative.parent.name == ".basedpyright":
            failures.append(f"{relative} is not allowed")
        if path.suffix not in {".py", ".pyi"}:
            continue
        try:
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if _SUPPRESSIONS.search(line):
                    failures.append(f"{relative}:{line_number} has an unruled Python suppression")
        except (OSError, UnicodeDecodeError) as exc:
            failures.append(f"cannot read {relative}: {exc}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Reject weaker Python type and lint policy.")
    parser.add_argument("--base", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    failures = check(args.root, args.base)
    if failures:
        print("Python policy check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Python type and lint policy is unchanged or stronger.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
