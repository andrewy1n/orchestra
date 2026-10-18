"""Locate the bundled ``project-design.json`` contract."""

from __future__ import annotations

import os
from pathlib import Path


def contract_path() -> Path:
    """Return the contract the CLI ships.

    ``ORCHESTRA_CONTRACT`` wins. In a checkout the packaged copy is a
    symlink to ``contract/project-design.json``, so both layouts report
    the same file.
    """
    candidates: list[Path] = []
    env = os.environ.get("ORCHESTRA_CONTRACT")
    if env:
        candidates.append(Path(env).expanduser())
    candidates.append(Path(__file__).resolve().parent / "data" / "project-design.json")
    candidates.append(Path(__file__).resolve().parents[1] / "contract" / "project-design.json")
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    searched = ", ".join(str(c) for c in candidates)
    raise FileNotFoundError(
        f"project-design.json not found (looked in {searched}); set ORCHESTRA_CONTRACT"
    )
