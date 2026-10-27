"""`.artifacts/config.json`: the marker and namespace list of a store."""

from __future__ import annotations

import json
from typing import Any

from canon.paths import validate_namespace

FORMAT = "canon/1"
CONFIG_NAME = "config.json"


class ConfigError(Exception):
    pass


def new_config(schemas: dict[str, str] | None = None) -> dict[str, Any]:
    return {"format": FORMAT, "schemas": dict(schemas or {}), "settings": {}}


def validate_config(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ConfigError("config.json must be a JSON object")
    if data.get("format") != FORMAT:
        raise ConfigError(f"unsupported store format {data.get('format')!r}; expected {FORMAT!r}")
    schemas = data.get("schemas")
    if not isinstance(schemas, dict):
        raise ConfigError("config.json schemas must be an object")
    for namespace, version in schemas.items():
        try:
            validate_namespace(namespace)
        except ValueError as exc:
            raise ConfigError(str(exc)) from exc
        if not isinstance(version, str) or not version:
            raise ConfigError(f"config.json schemas.{namespace} must be a version string")
    settings = data.get("settings", {})
    if not isinstance(settings, dict):
        raise ConfigError("config.json settings must be an object")
    return data


def dump_config(config: dict[str, Any]) -> str:
    return json.dumps(config, indent=2) + "\n"
