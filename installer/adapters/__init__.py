"""Adapter registry.

Native adapters register by provider id:

    @register_adapter("claude")
    class ClaudeAdapter(BaseAdapter):
        ...

A ``kind: skills`` matrix row uses :class:`SkillsCliAdapter` without a
registration line. Everything else keeps :class:`GenericSkillsAdapter`, so a
new matrix row works before its native adapter exists.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from installer.adapters.base import Adapter, BaseAdapter
from installer.adapters.tail import SkillsCliAdapter
from installer.model import Provider

AdapterFactory = Callable[..., Adapter]

_REGISTRY: dict[str, AdapterFactory] = {}


def register_adapter(provider_id: str) -> Callable[[AdapterFactory], AdapterFactory]:
    """Register an adapter class for one matrix provider id."""

    def decorator(factory: AdapterFactory) -> AdapterFactory:
        if provider_id in _REGISTRY:
            raise ValueError(f"adapter for {provider_id!r} is already registered")
        _REGISTRY[provider_id] = factory
        return factory

    return decorator


def registered_adapters() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))


def build_adapter(
    provider: Provider,
    *,
    base: Path,
    scope: str,
    mode: str,
    source_root: Path,
) -> Adapter:
    """Instantiate the registered adapter, the skills-CLI tail, or the generic one.

    Native rows win by id. A ``kind: skills`` row delegates to
    :class:`SkillsCliAdapter` without needing a registration line, so adding a
    tail host is a matrix edit. Anything else keeps the generic behaviour.
    """
    factory = _REGISTRY.get(provider.id)
    if factory is None:
        factory = SkillsCliAdapter if provider.kind == "skills" else GenericSkillsAdapter
    return factory(
        provider,
        base=base,
        scope=scope,
        mode=mode,
        source_root=source_root,
    )


class GenericSkillsAdapter(BaseAdapter):
    """Copy or symlink the allowlisted payload into a host skills directory."""


# Importing the native module runs its @register_adapter decorators. It comes
# last because those modules import the registry above.
from installer.adapters import native as _native  # noqa: E402,F401
from installer.adapters.native import (  # noqa: E402
    ClaudeAdapter,
    CursorAdapter,
    NativeAdapter,
    OpenCodeAdapter,
)


__all__ = [
    "Adapter",
    "BaseAdapter",
    "ClaudeAdapter",
    "CursorAdapter",
    "GenericSkillsAdapter",
    "NativeAdapter",
    "OpenCodeAdapter",
    "SkillsCliAdapter",
    "build_adapter",
    "register_adapter",
    "registered_adapters",
]
