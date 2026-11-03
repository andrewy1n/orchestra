"""Catalog for installed Orchestra plugins."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import metadata
from typing import Literal, TypeGuard

from orchestra.canon.types import JsonObject

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


@dataclass(frozen=True)
class PluginExecutionIdentity:
    payload: JsonObject
    digest: str


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
            if registration.descriptor.api_version != PLUGIN_API_VERSION:
                raise PluginCatalogError(
                    f"plugin {plugin_id!r} uses unsupported API version "
                    f"{registration.descriptor.api_version!r}"
                )
            return registration
    raise PluginCatalogError(f"unknown {scope} plugin: {plugin_id}")


def compute_execution_identity(
    descriptor: PluginDescriptor,
    parameters: JsonObject,
    execution_definition: JsonObject,
) -> PluginExecutionIdentity:
    payload: JsonObject = {
        "format_version": 1,
        "scope": descriptor.scope,
        "plugin_id": descriptor.plugin_id,
        "entry_point_target": descriptor.target,
        "distribution_name": descriptor.distribution,
        "distribution_version": descriptor.version,
        "api_version": descriptor.api_version,
        "parameters": parameters,
        "execution_definition": execution_definition,
    }
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    payload["digest"] = digest
    return PluginExecutionIdentity(payload=payload, digest=digest)


def _registrations(scope: PluginScope) -> tuple[PluginRegistration, ...]:
    group = PLUGIN_GROUPS[scope]
    entries = metadata.entry_points(group=group)
    registrations: list[PluginRegistration] = []
    for entry in entries:
        distribution = entry.dist
        if distribution is None:
            raise PluginCatalogError(f"plugin entry point {entry.name!r} has no distribution")
        name = _metadata_value(distribution, "Name")
        version = distribution.version
        if not name or not version:
            raise PluginCatalogError(
                f"plugin entry point {entry.name!r} has no distribution identity"
            )
        api_version = _metadata_value(distribution, "Orchestra-Plugin-API")
        config_shape = _config_shape(
            _metadata_value(distribution, "Orchestra-Plugin-Config") or "{}", entry.name
        )
        descriptor = PluginDescriptor(
            scope=scope,
            plugin_id=entry.name,
            target=entry.value,
            distribution=name,
            version=version,
            api_version=api_version or PLUGIN_API_VERSION,
            config_shape=config_shape,
        )
        registrations.append(PluginRegistration(descriptor, entry))
    return tuple(registrations)


def _config_shape(raw: str, plugin_id: str) -> Mapping[str, object]:
    try:
        shape = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PluginCatalogError(f"invalid config shape for plugin {plugin_id!r}: {exc}") from exc
    if not _is_string_mapping(shape):
        raise PluginCatalogError(f"config shape for plugin {plugin_id!r} must be a JSON object")
    return shape


def _metadata_value(
    distribution: metadata.Distribution,
    key: str,
    default: str | None = None,
) -> str | None:
    value: object = distribution.metadata.get(key, default)  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]  # PackageMetadata implements get at runtime; typeshed omits it.
    return value if isinstance(value, str) else default


def _is_string_mapping(value: object) -> TypeGuard[dict[str, object]]:
    if not isinstance(value, dict):
        return False
    return all(isinstance(key, str) for key in value)  # pyright: ignore[reportUnknownVariableType]  # JSON keys are dynamic until validated.


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
