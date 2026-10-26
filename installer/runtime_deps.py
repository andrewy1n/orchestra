"""Install declared runtime dependencies into this interpreter."""

from __future__ import annotations

import importlib
import importlib.metadata
import re
import subprocess
import sys

_EVIDENCE_EXTRA = re.compile(r"""\bextra\s*==\s*(['"])evidence\1""")


def _canon_importable() -> bool:
    try:
        importlib.import_module("canon")
    except ImportError:
        for name in list(sys.modules):
            if name == "canon" or name.startswith("canon."):
                sys.modules.pop(name, None)
        return False
    return True


def _names_evidence_extra(requirement: str) -> bool:
    return _EVIDENCE_EXTRA.search(requirement.partition(";")[2]) is not None


def _runtime_requirement_specs() -> list[str]:
    """Installed ``requires()``, without requirements marked for the evidence extra."""
    try:
        raw = importlib.metadata.requires("orchestra")
    except importlib.metadata.PackageNotFoundError:
        return []
    if not raw:
        return []
    specs: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        spec = item.strip()
        if spec and not _names_evidence_extra(spec):
            specs.append(spec)
    return specs


def ensure_runtime_deps() -> None:
    """Install runtime dependencies unless ``canon`` already imports.

    Drops every requirement whose marker names the evidence extra, then runs
    ``uv pip install --python`` this interpreter on what remains. Never installs
    the evidence extra. An interpreter that can already import
    ``canon`` skips the install so host tests do not use the network.
    """
    if _canon_importable():
        return
    specs = _runtime_requirement_specs()
    if not specs:
        return
    command = ["uv", "pip", "install", "--python", sys.executable, *specs]
    try:
        completed = subprocess.run(command, check=False)
    except FileNotFoundError:
        print(
            "orchestra install: uv is required to install runtime dependencies",
            file=sys.stderr,
        )
        return
    if completed.returncode != 0:
        print(
            "orchestra install: failed to install runtime dependencies",
            file=sys.stderr,
        )
        return
    importlib.invalidate_caches()
