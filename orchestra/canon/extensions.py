"""Catalog for installed Orchestra plugins."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import metadata
from typing import Literal

PluginScope = Literal["composer.ideas", "tuner.verify", "conductor.land"]
PLUGIN_GROUPS: Mapping[PluginScope, str] = {
    "composer.ideas": "orchestra.composer.ideas",
    "tuner.verify": "orchestra.tuner.verify",
    "conductor.land": "orchestra.conductor.land",
}
PLUGIN_API_VERSION = "1"


class PluginCatalogError(ValueError):
    """An installed plugin catalog is invalid or cannot resolve a plugin."""


@dataclass(frozen=True)
class PluginDescriptor:
    scope: PluginScope
    plugin_id: str
    target: str
    distribution: str
    version: str
    api_version: str
    config_shape: Mapping[str, object]


@dataclass(frozen=True)
class PluginRegistration:
    descriptor: PluginDescriptor
    entry_point: metadata.EntryPoint

    def load(self) -> object:
        return self.entry_point.load()


def list_plugins(scope: PluginScope | None = None) -> tuple[PluginDescriptor, ...]:
    selected_scopes = (scope,) if scope is not None else tuple(PLUGIN_GROUPS)
    registrations = tuple(
        registration
        for selected_scope in selected_scopes
        for registration in _registrations(selected_scope)
    )
    _reject_duplicates(registrations)
    return tuple(registration.descriptor for registration in registrations)


def resolve_plugin(scope: PluginScope, plugin_id: str) -> PluginRegistration:
    registrations = _registrations(scope)
    _reject_duplicates(registrations)
    for registration in registrations:
        if registration.descriptor.plugin_id == plugin_id:
            return registration
    raise PluginCatalogError(f"unknown {scope} plugin: {plugin_id}")


def _registrations(scope: PluginScope) -> tuple[PluginRegistration, ...]:
    group = PLUGIN_GROUPS[scope]
    entries = metadata.entry_points(group=group)
    registrations: list[PluginRegistration] = []
    for entry in entries:
        distribution = entry.dist
        if distribution is None:
            raise PluginCatalogError(f"plugin entry point {entry.name!r} has no distribution")
        name = distribution.metadata.get("Name")
        version = distribution.version
        if not name or not version:
            raise PluginCatalogError(
                f"plugin entry point {entry.name!r} has no distribution identity"
            )
        api_version = distribution.metadata.get("Orchestra-Plugin-API", PLUGIN_API_VERSION)
        config_shape = _config_shape(
            distribution.metadata.get("Orchestra-Plugin-Config", "{}"), entry.name
        )
        descriptor = PluginDescriptor(
            scope=scope,
            plugin_id=entry.name,
            target=entry.value,
            distribution=name,
            version=version,
            api_version=api_version,
            config_shape=config_shape,
        )
        registrations.append(PluginRegistration(descriptor, entry))
    return tuple(registrations)


def _config_shape(raw: str, plugin_id: str) -> Mapping[str, object]:
    try:
        shape = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PluginCatalogError(f"invalid config shape for plugin {plugin_id!r}: {exc}") from exc
    if not isinstance(shape, dict) or any(not isinstance(key, str) for key in shape):
        raise PluginCatalogError(f"config shape for plugin {plugin_id!r} must be a JSON object")
    return shape


def _reject_duplicates(registrations: tuple[PluginRegistration, ...]) -> None:
    seen: set[tuple[PluginScope, str]] = set()
    for registration in registrations:
        descriptor = registration.descriptor
        key = (descriptor.scope, descriptor.plugin_id)
        if key in seen:
            raise PluginCatalogError(
                f"duplicate plugin id {descriptor.plugin_id!r} in {descriptor.scope}"
            )
        seen.add(key)
