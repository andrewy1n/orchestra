"""Orchestration plugin. Evidence gates stay in the affidavit package."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def _candidate_affidavit_roots() -> list[Path]:
    roots: list[Path] = []
    env = os.environ.get("AFFIDAVIT_ROOT")
    if env:
        roots.append(Path(env).expanduser())
    aff = shutil.which("aff")
    if aff:
        # bin/aff lives one directory under the affidavit checkout.
        roots.append(Path(aff).resolve().parent.parent)
    repo_parent = Path(__file__).resolve().parents[1].parent
    roots.append(repo_parent / "affidavit")
    roots.append(Path.home() / "affidavit")
    return roots


def ensure_affidavit_importable() -> None:
    """Put the affidavit checkout on sys.path when cwd is not that checkout.

    ``import affidavit`` succeeds there because the empty path entry is the
    cwd. Orchestra still imports ``affidavit.aa``, ``affidavit.check``, and
    ``affidavit.policy`` from other working directories.
    """
    try:
        import affidavit  # noqa: F401
    except ModuleNotFoundError:
        pass
    else:
        return
    for root in _candidate_affidavit_roots():
        if (root / "affidavit" / "__init__.py").is_file():
            entry = str(root.resolve())
            if entry not in sys.path:
                sys.path.append(entry)
            return


ensure_affidavit_importable()
