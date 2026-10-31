"""The installer's copy allowlist.

Only these repository roots may reach an install destination. The list is
deliberately closed: adding a root means a deliberate edit here and a test
change, not an accident in a recursive copy.

``.canon/`` and ``.worktrees/`` are never install inputs. ``dashboard/``
is a checkout-side developer tool, not a host payload, and carries store
state at runtime, so it stays out too.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

#: Top-level roots copied for every provider.
COPY_ALLOWLIST: tuple[str, ...] = ("skills", "agents")

#: Per-provider roots, relative to the repository root.
HOST_ALLOWLIST = "hosts/{provider}"

#: Never copied, never linked, never traversed by the installer.
DENY_ROOTS: tuple[str, ...] = (".canon", ".worktrees", "dashboard")

#: Housekeeping that never belongs in a host payload.
IGNORE_NAMES: tuple[str, ...] = ("__pycache__", ".DS_Store", ".pytest_cache")
IGNORE_SUFFIXES: tuple[str, ...] = (".pyc", ".pyo")


def allowed_roots(provider_id: str) -> tuple[str, ...]:
    """Source roots this provider may install, in matrix-independent order."""
    return (*COPY_ALLOWLIST, HOST_ALLOWLIST.format(provider=provider_id))


def is_allowed(relative: Path | str, provider_id: str) -> bool:
    """True when ``relative`` is inside one of :func:`allowed_roots`."""
    relative_path = PurePosixPath(str(relative).replace("\\", "/"))
    parts = relative_path.parts
    if not parts or relative_path.is_absolute():
        return False
    if any(part == ".." for part in parts):
        return False
    if parts[0] in DENY_ROOTS:
        return False
    if parts[0] in COPY_ALLOWLIST:
        return True
    if len(parts) >= 2 and parts[0] == "hosts" and parts[1] == provider_id:
        return True
    return False


def assert_allowed(relative: Path | str, provider_id: str) -> None:
    if not is_allowed(relative, provider_id):
        raise ValueError(f"installer allowlist rejects {relative!s} for provider {provider_id!r}")
