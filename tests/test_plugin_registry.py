from __future__ import annotations

from types import SimpleNamespace

import pytest

import orchestra.canon.extensions as extensions


def _entry_point(name: str, target: str, distribution: str) -> SimpleNamespace:
    metadata_entries = (
        SimpleNamespace(name="version", value="1", group=extensions.PLUGIN_API_GROUP),
        SimpleNamespace(name=name, value="{}", group=extensions.PLUGIN_CONFIG_GROUP),
    )
    return SimpleNamespace(
        name=name,
        value=target,
        dist=SimpleNamespace(
            metadata={"Name": distribution},
            version="1.2.3",
            entry_points=metadata_entries,
        ),
        load=lambda: target,
    )


def _install_entries(
    monkeypatch: pytest.MonkeyPatch,
    entries: dict[str, tuple[SimpleNamespace, ...]],
) -> None:
    def discover(*, group: str) -> tuple[SimpleNamespace, ...]:
        return entries.get(group, ())

    monkeypatch.setattr(extensions.metadata, "entry_points", discover)


def test_catalog_lists_same_id_in_separate_scopes_without_loading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    loaded: list[str] = []
    idea = _entry_point("shared", "ideas:Source", "idea-provider")
    verify = _entry_point("shared", "verify:Technique", "verify-provider")
    landing = _entry_point("shared", "land:Adapter", "land-provider")
    idea.load = lambda: loaded.append("ideas")
    verify.load = lambda: loaded.append("verify")
    landing.load = lambda: loaded.append("land")
    _install_entries(
        monkeypatch,
        {
            "orchestra.composer.ideas": (idea,),
            "orchestra.tuner.verify": (verify,),
            "orchestra.conductor.land": (landing,),
        },
    )

    descriptors = extensions.list_plugins()

    assert [(item.scope, item.plugin_id) for item in descriptors] == [
        ("composer.ideas", "shared"),
        ("tuner.verify", "shared"),
        ("conductor.land", "shared"),
    ]
    assert loaded == []


def test_catalog_rejects_duplicate_ids_within_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_entries(
        monkeypatch,
        {
            "orchestra.tuner.verify": (
                _entry_point("duplicate", "one:Plugin", "one"),
                _entry_point("duplicate", "two:Plugin", "two"),
            )
        },
    )

    with pytest.raises(extensions.PluginCatalogError, match="duplicate plugin id"):
        extensions.list_plugins("tuner.verify")


def test_resolve_loads_only_the_selected_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
    loaded: list[str] = []
    first = _entry_point("first", "one:Plugin", "one")
    second = _entry_point("second", "two:Plugin", "two")
    first.load = lambda: loaded.append("first")
    second.load = lambda: loaded.append("second")
    _install_entries(monkeypatch, {"orchestra.tuner.verify": (first, second)})

    registration = extensions.resolve_plugin("tuner.verify", "second")

    assert registration.descriptor.distribution == "two"
    assert registration.load() is None
    assert loaded == ["second"]


def test_resolve_rejects_unsupported_api_version(monkeypatch: pytest.MonkeyPatch) -> None:
    plugin = _entry_point("plugin", "plugin:Plugin", "plugin")
    plugin.dist.entry_points = (
        SimpleNamespace(name="v2", value="plugin:Plugin", group=extensions.PLUGIN_API_GROUP),
        SimpleNamespace(name="plugin", value="{}", group=extensions.PLUGIN_CONFIG_GROUP),
    )
    _install_entries(monkeypatch, {"orchestra.tuner.verify": (plugin,)})

    with pytest.raises(extensions.PluginCatalogError, match="unsupported API version '2'"):
        extensions.resolve_plugin("tuner.verify", "plugin")


def test_resolve_requires_an_api_version_marker(monkeypatch: pytest.MonkeyPatch) -> None:
    plugin = _entry_point("plugin", "plugin:Plugin", "plugin")
    plugin.dist.entry_points = (
        SimpleNamespace(name="plugin", value="{}", group=extensions.PLUGIN_CONFIG_GROUP),
    )
    _install_entries(monkeypatch, {"orchestra.tuner.verify": (plugin,)})

    with pytest.raises(extensions.PluginCatalogError, match=r"must declare orchestra\.plugin_api"):
        extensions.resolve_plugin("tuner.verify", "plugin")


def test_plugin_config_shape_checks_required_fields_and_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plugin = _entry_point("plugin", "plugin:Plugin", "plugin")
    plugin.dist.entry_points = (
        SimpleNamespace(name="version", value="1", group=extensions.PLUGIN_API_GROUP),
        SimpleNamespace(
            name="plugin",
            value='{"type":"object","properties":{"mode":{"type":"string"}},"required":["mode"],"additionalProperties":false}',
            group=extensions.PLUGIN_CONFIG_GROUP,
        ),
    )
    _install_entries(monkeypatch, {"orchestra.tuner.verify": (plugin,)})
    shape = extensions.resolve_plugin("tuner.verify", "plugin").descriptor.config_shape

    with pytest.raises(extensions.PluginCatalogError, match="missing required fields: mode"):
        extensions.validate_plugin_config("plugin", shape, {})
    with pytest.raises(extensions.PluginCatalogError, match="invalid type"):
        extensions.validate_plugin_config("plugin", shape, {"mode": True})
    with pytest.raises(extensions.PluginCatalogError, match="unknown fields: extra"):
        extensions.validate_plugin_config("plugin", shape, {"mode": "safe", "extra": "x"})
