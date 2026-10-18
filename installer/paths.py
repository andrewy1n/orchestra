"""Where the installer reads its payload from."""

from __future__ import annotations

import os
from pathlib import Path

SOURCE_ENV = "ORCHESTRA_INSTALL_SOURCE"


def source_root() -> Path:
    """Repository root holding ``skills/``, ``contract/``, ``agents/``, ``hosts/``.

    ``ORCHESTRA_INSTALL_SOURCE`` lets tests point at a fixture tree; otherwise
    the checkout containing this package is the source of truth.
    """
    override = os.environ.get(SOURCE_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[1]
