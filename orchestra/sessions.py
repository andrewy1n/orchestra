"""Session metrics behind ``orchestra sessions``.

The implementation lives in ``scripts/session_report.py`` and
``scripts/session_aggregate.py``; the package ships that directory as
``orchestra/_scripts`` so an installed console script works outside a
checkout. ``ORCHESTRA_SCRIPTS`` overrides the location.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path


def scripts_dir() -> Path:
    """Return the directory holding ``session_report.py``."""
    candidates: list[Path] = []
    env = os.environ.get("ORCHESTRA_SCRIPTS")
    if env:
        candidates.append(Path(env).expanduser())
    candidates.append(Path(__file__).resolve().parent / "_scripts")
    candidates.append(Path(__file__).resolve().parents[1] / "scripts")
    for candidate in candidates:
        if (candidate / "session_report.py").is_file():
            return candidate
    searched = ", ".join(str(c) for c in candidates)
    raise FileNotFoundError(
        f"session scripts not found (looked in {searched}); set ORCHESTRA_SCRIPTS"
    )


def _load(name: str):
    directory = str(scripts_dir())
    if directory not in sys.path:
        sys.path.insert(0, directory)
    return importlib.import_module(name)


def report(root: str | Path | None = None, *, records: bool = False) -> int:
    """Print one JSON summary per transcript under ``root``."""
    argv: list[str] = []
    if records:
        argv.append("--records")
    if root is not None:
        argv.append(str(root))
    return _load("session_report").main(argv)


def aggregate(report_path: str | Path | None = None) -> int:
    """Print one aggregate document for a report JSONL file (or stdin)."""
    # session_aggregate.main() expects a script-name slot at argv[0].
    argv = ["orchestra sessions aggregate"]
    if report_path is not None and str(report_path) != "-":
        argv.append(str(report_path))
    return _load("session_aggregate").main(argv)
