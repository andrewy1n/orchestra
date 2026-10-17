"""Align a design file's top-level project id with orchestra."""

from __future__ import annotations

import json
import re
from pathlib import Path

CURRENT = "current"
REWRITTEN = "rewritten"
STOPPED = "stopped"

_AFFIDAVIT_PROJECT = re.compile(r'("project"\s*:\s*")affidavit(")')


def rewrite_project_field(design_path: str | Path) -> str:
    """Return current, rewritten, or stopped.

    ``orchestra`` is already current and the file is left untouched.
    ``affidavit`` is rewritten to ``orchestra`` in place.
    Any other value is left unchanged and reported as stopped.
    """
    path = Path(design_path)
    text = path.read_text(encoding="utf-8")
    project = json.loads(text).get("project")
    if project == "orchestra":
        return CURRENT
    if project != "affidavit":
        return STOPPED
    new_text, count = _AFFIDAVIT_PROJECT.subn(r"\1orchestra\2", text, count=1)
    if count != 1 or json.loads(new_text).get("project") != "orchestra":
        raise ValueError(f"could not rewrite project field in {path}")
    path.write_text(new_text, encoding="utf-8")
    return REWRITTEN
