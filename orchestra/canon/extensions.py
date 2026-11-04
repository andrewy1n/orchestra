"""Catalog for installed Orchestra plugins."""

from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import metadata
from typing import Literal, TypeGuard

from orchestra.canon.types import JsonObject, JsonValue

PluginScope = Literal["composer.ideas", "tuner.verify", "conductor.land"]
PLUGIN_GROUPS: Mapping[PluginScope, str] = {
    "composer.ideas": "orchestra.composer.ideas",
    "tuner.verify": "orchestra.tuner.verify",
    "conductor.land": "orchestra.conductor.land",
}
PLUGIN_API_VERSION = "1"
PLUGIN_API_GROUP = "orchestra.plugin_api"
PLUGIN_CONFIG_GROUP = "orchestra.plugin_config"


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
        try:
            name: str | None = distribution.metadata["Name"]
        except KeyError:
            name = None
        version = distribution.version
        if not name or not version:
            raise PluginCatalogError(
                f"plugin entry point {entry.name!r} has no distribution identity"
            )
        api_version = _distribution_plugin_value(distribution, PLUGIN_API_GROUP, "v1")
        config_shape_raw = _distribution_plugin_value(distribution, PLUGIN_CONFIG_GROUP, entry.name)
        if api_version is None:
            raise PluginCatalogError(
                f"distribution {name!r} must declare {PLUGIN_API_GROUP}.version"
            )
        if config_shape_raw is None:
            raise PluginCatalogError(
                f"distribution {name!r} must declare {PLUGIN_CONFIG_GROUP}.{entry.name}"
            )
        config_shape = _config_shape(config_shape_raw, entry.name)
        descriptor = PluginDescriptor(
            scope=scope,
            plugin_id=entry.name,
            target=entry.value,
            distribution=name,
            version=version,
            api_version=api_version or "",
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
    _validate_config_shape(shape, plugin_id)
    return shape


def _distribution_plugin_value(
    distribution: metadata.Distribution,
    group: str,
    name: str,
) -> str | None:
    if group == PLUGIN_API_GROUP:
        values = tuple(
            entry.name.removeprefix("v")
            if entry.name.startswith("v") and entry.name[1:].isdigit()
            else entry.value
            for entry in distribution.entry_points
            if entry.group == group
            and (
                (entry.name.startswith("v") and entry.name[1:].isdigit()) or entry.name == "version"
            )
        )
    elif group == PLUGIN_CONFIG_GROUP:
        values = tuple(
            _decode_config_shape(entry.name.removeprefix(f"{name}__"))
            if entry.name.startswith(f"{name}__")
            else entry.value
            for entry in distribution.entry_points
            if entry.group == group and (entry.name.startswith(f"{name}__") or entry.name == name)
        )
    else:
        values = ()
    if len(values) != 1:
        return None
    return values[0]


def _decode_config_shape(encoded: str) -> str:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(encoded + padding).decode("utf-8")


def validate_plugin_config(
    plugin_id: str,
    config_shape: Mapping[str, object],
    config: JsonObject,
) -> None:
    properties_value = config_shape.get("properties", {})
    if not _is_string_mapping(properties_value):
        raise PluginCatalogError(f"config shape for plugin {plugin_id!r} has invalid properties")
    required_value = config_shape.get("required", [])
    if not _is_string_list(required_value):
        raise PluginCatalogError(f"config shape for plugin {plugin_id!r} has invalid required list")
    missing = [key for key in required_value if key not in config]
    if missing:
        raise PluginCatalogError(
            f"plugin {plugin_id!r} config is missing required fields: {', '.join(missing)}"
        )
    additional_value = config_shape.get("additionalProperties", True)
    if not isinstance(additional_value, bool):
        raise PluginCatalogError(
            f"config shape for plugin {plugin_id!r} has invalid additionalProperties"
        )
    if not additional_value:
        extra = [key for key in config if key not in properties_value]
        if extra:
            raise PluginCatalogError(
                f"plugin {plugin_id!r} config has unknown fields: {', '.join(extra)}"
            )
    for key, value in config.items():
        schema = properties_value.get(key)
        if schema is None:
            continue
        if not _is_string_mapping(schema):
            raise PluginCatalogError(
                f"config shape for plugin {plugin_id!r} has invalid field {key!r}"
            )
        value_type = schema.get("type")
        if not isinstance(value_type, str) or not _matches_config_type(value, value_type):
            raise PluginCatalogError(f"plugin {plugin_id!r} config field {key!r} has invalid type")


def _validate_config_shape(shape: Mapping[str, object], plugin_id: str) -> None:
    value_type = shape.get("type", "object")
    if value_type != "object":
        raise PluginCatalogError(f"config shape for plugin {plugin_id!r} must describe an object")
    properties = shape.get("properties", {})
    required = shape.get("required", [])
    additional = shape.get("additionalProperties", True)
    if not _is_string_mapping(properties) or not _is_string_list(required):
        raise PluginCatalogError(f"config shape for plugin {plugin_id!r} is malformed")
    if not isinstance(additional, bool):
        raise PluginCatalogError(f"config shape for plugin {plugin_id!r} is malformed")
    for key, value in properties.items():
        if not _is_string_mapping(value):
            raise PluginCatalogError(
                f"config shape for plugin {plugin_id!r} has an invalid property {key!r}"
            )
        field_type = value.get("type")
        if not isinstance(field_type, str) or field_type not in {
            "array",
            "boolean",
            "integer",
            "null",
            "number",
            "object",
            "string",
        }:
            raise PluginCatalogError(
                f"config shape for plugin {plugin_id!r} has an invalid property type for {key!r}"
            )


def _matches_config_type(value: JsonValue, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "null":
        return value is None
    return False


def _is_string_list(value: object) -> TypeGuard[list[str]]:
    return isinstance(value, list) and all(
        isinstance(item, str)
        for item in value  # pyright: ignore[reportUnknownVariableType]  # JSON schema values are dynamic until validated.
    )


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
