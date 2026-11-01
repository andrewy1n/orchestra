"""Where the installer reads its payload from."""

from __future__ import annotations

import os
from pathlib import Path

SOURCE_ENV = "ORCHESTRA_INSTALL_SOURCE"


def _checkout_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _payload_root() -> Path:
    return Path(__file__).resolve().parent / "payload"


def _resolve_source() -> tuple[Path, bool]:
    """Source directory, and whether resolution fell through to the payload.

    ``ORCHESTRA_INSTALL_SOURCE`` wins. Otherwise the checkout is used when
    ``skills/`` sits beside this package. The packaged ``payload/`` directory
    is the fallback, and only that fallback is packaged.
    """
    override = os.environ.get(SOURCE_ENV)
    if override:
        return Path(override).expanduser().resolve(), False
    checkout = _checkout_root()
    if (checkout / "skills").is_dir():
        return checkout, False
    return _payload_root().resolve(), True


def source_root() -> Path:
    """Directory holding ``skills/``, ``agents/``, and ``hosts/``."""
    root, _packaged = _resolve_source()
    return root


def is_packaged() -> bool:
    """True only when ``source_root`` fell through to ``installer/payload``."""
    _root, packaged = _resolve_source()
    return packaged
