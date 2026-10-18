"""Adapter registry.

Native adapters register by provider id:

    @register_adapter("claude")
    class ClaudeAdapter(BaseAdapter):
        ...

Everything not registered keeps :class:`GenericSkillsAdapter`, so a new
matrix row works before its native adapter exists.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from installer.adapters.base import Adapter, BaseAdapter
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
    """Instantiate the registered adapter, or the generic one."""
    factory = _REGISTRY.get(provider.id, GenericSkillsAdapter)
    return factory(
        provider,
        base=base,
        scope=scope,
        mode=mode,
        source_root=source_root,
    )


class GenericSkillsAdapter(BaseAdapter):
    """Copy or symlink the allowlisted payload into a host skills directory."""


__all__ = [
    "Adapter",
    "BaseAdapter",
    "GenericSkillsAdapter",
    "build_adapter",
    "register_adapter",
    "registered_adapters",
]
