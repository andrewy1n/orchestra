from __future__ import annotations

import pytest

from orchestra.canon.extensions import PluginCatalogError, resolve_plugin, validate_plugin_config
from orchestra.canon.types import JsonObject


def _validate(config: JsonObject) -> None:
    descriptor = resolve_plugin("conductor.land", "github-pr").descriptor
    validate_plugin_config("github-pr", descriptor.config_shape, config)


def test_schema_rejects_token_env() -> None:
    with pytest.raises(PluginCatalogError, match="token_env"):
        _validate({"token_env": "X"})


def test_schema_accepts_repository() -> None:
    _validate({"repository": "o/r"})


def test_schema_accepts_remote() -> None:
    _validate({"remote": "origin"})
