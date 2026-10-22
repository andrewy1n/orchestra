"""Package metadata for declared install (R1, R4).

Reads the orchestra, affidavit, and adaptive-artifacts ``pyproject.toml`` files.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def _pyproject_paths() -> dict[str, Path]:
    """The three project files this phase's metadata tests read."""
    if os.environ.get("AFFIDAVIT_ROOT"):
        affidavit_root = Path(os.environ["AFFIDAVIT_ROOT"]).expanduser()
    else:
        affidavit_root = Path.home() / "affidavit"
    if os.environ.get("ADAPTIVE_ARTIFACTS_ROOT"):
        adaptive_root = Path(os.environ["ADAPTIVE_ARTIFACTS_ROOT"]).expanduser()
    else:
        adaptive_root = Path.home() / "adaptive-artifacts"
    return {
        "orchestra": _ROOT / "pyproject.toml",
        "affidavit": affidavit_root / "pyproject.toml",
        "adaptive-artifacts": adaptive_root / "pyproject.toml",
    }


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _load_toml(text: str) -> dict:
    if not text.strip():
        return {}
    try:
        import tomllib
    except ModuleNotFoundError:
        tomllib = None
    try:
        if tomllib is not None:
            loaded = tomllib.loads(text)
        else:
            import tomli

            loaded = tomli.loads(text)
    except Exception:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _normalize_dep(spec: str) -> str:
    match = re.match(r"\s*([A-Za-z0-9_.-]+)", spec)
    raw = match.group(1) if match else spec.strip()
    return raw.replace("_", "-").lower()


def _dependency_names(text: str) -> list[str]:
    data = _load_toml(text)
    project = data.get("project") if isinstance(data, dict) else None
    deps = project.get("dependencies") if isinstance(project, dict) else None
    if not isinstance(deps, list):
        return []
    return [_normalize_dep(str(item)) for item in deps]


def _extra_names(text: str, extra: str) -> list[str]:
    data = _load_toml(text)
    project = data.get("project") if isinstance(data, dict) else None
    extras = project.get("optional-dependencies") if isinstance(project, dict) else None
    values = extras.get(extra) if isinstance(extras, dict) else None
    if not isinstance(values, list):
        return []
    return [_normalize_dep(str(item)) for item in values]


def _read_projects() -> dict[str, str]:
    return {name: _read(path) for name, path in _pyproject_paths().items()}


def test_r1_affidavit_depends_on_adaptive_artifacts():
    """R1: the affidavit package declares a dependency on adaptive-artifacts."""
    paths = _pyproject_paths()
    texts = _read_projects()
    deps = _dependency_names(texts["affidavit"])
    assert "adaptive-artifacts" in deps, (
        f"{paths['affidavit']} dependencies={deps!r}; "
        f"also read {paths['orchestra']} and {paths['adaptive-artifacts']}"
    )


def test_r4_evidence_extra_depends_on_affidavit():
    """R4: the orchestra evidence extra declares a dependency on affidavit."""
    paths = _pyproject_paths()
    texts = _read_projects()
    evidence = _extra_names(texts["orchestra"], "evidence")
    assert "affidavit" in evidence, (
        f"{paths['orchestra']} evidence extra={evidence!r}; "
        f"also read {paths['affidavit']} and {paths['adaptive-artifacts']}"
    )
