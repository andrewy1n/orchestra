"""`.canon/config.json`: the marker and namespace list of a store."""

from __future__ import annotations

import json

from orchestra.canon.paths import validate_namespace
from orchestra.canon.types import JsonObject, JsonValue, get_object

FORMAT = "canon/1"
CONFIG_NAME = "config.json"


class ConfigError(Exception):
    pass


def new_config(schemas: dict[str, str] | None = None) -> JsonObject:
    return {"format": FORMAT, "schemas": dict(schemas or {}), "settings": {}}


def validate_config(data: JsonValue) -> JsonObject:
    config = get_object({"config": data}, "config")
    if config is None:
        raise ConfigError("config.json must be a JSON object")
    format_value = config.get("format")
    if format_value != FORMAT:
        raise ConfigError(f"unsupported store format {format_value!r}; expected {FORMAT!r}")
    schemas = get_object(config, "schemas")
    if schemas is None:
        raise ConfigError("config.json schemas must be an object")
    for namespace, version in schemas.items():
        try:
            validate_namespace(namespace)
        except ValueError as exc:
            raise ConfigError(str(exc)) from exc
        if not isinstance(version, str) or not version:
            raise ConfigError(f"config.json schemas.{namespace} must be a version string")
    settings = config.get("settings", {})
    if get_object({"settings": settings}, "settings") is None:
        raise ConfigError("config.json settings must be an object")
    return config


def dump_config(config: JsonObject) -> str:
    return json.dumps(config, indent=2) + "\n"
