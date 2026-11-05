"""Adapter registry.

Native adapters register by provider id:

    @register_adapter("claude")
    class ClaudeAdapter(BaseAdapter):
        ...

Skills and directory rows select their adapters by kind.
"""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
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
    if provider.kind == "skills":
        factory = SkillsCliAdapter
    elif provider.kind == "directory":
        factory = GenericSkillsAdapter
    elif provider.native and provider.id in _REGISTRY:
        factory = _REGISTRY[provider.id]
    else:
        raise ValueError(f"no {provider.kind!r} adapter for {provider.id!r}")
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
import_module("installer.adapters.native")
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
