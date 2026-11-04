from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, TypeGuard, runtime_checkable

from orchestra.canon.extensions import PluginCatalogError, resolve_plugin, validate_plugin_config
from orchestra.canon.types import JsonObject


@dataclass(frozen=True)
class IdeaSourceRequest:
    parameters: JsonObject


@dataclass(frozen=True)
class IdeaSourceItem:
    external_id: str
    title: str
    body: str
    url: str
    updated_at: str
    labels: tuple[str, ...]


@runtime_checkable
class IdeaSource(Protocol):
    def list_ideas(self, request: IdeaSourceRequest) -> Sequence[IdeaSourceItem]: ...


def fetch_plugin_ideas(plugin_id: str, parameters: JsonObject) -> tuple[IdeaSourceItem, ...]:
    try:
        registration = resolve_plugin("composer.ideas", plugin_id)
    except PluginCatalogError as exc:
        raise ValueError(str(exc)) from exc
    validate_plugin_config(plugin_id, registration.descriptor.config_shape, parameters)
    factory = registration.load()
    if not callable(factory):
        raise ValueError(f"idea source {plugin_id!r} is not constructible")
    source = factory()
    if not isinstance(source, IdeaSource):
        raise ValueError(f"idea source {plugin_id!r} has no list_ideas method")
    return validate_idea_source_items(source.list_ideas(IdeaSourceRequest(parameters)))


def validate_idea_source_items(items: object) -> tuple[IdeaSourceItem, ...]:
    if not _is_item_sequence(items):
        raise ValueError("idea source output must be a sequence of IdeaSourceItem values")
    result: list[IdeaSourceItem] = []
    for item in items:
        if not isinstance(item, IdeaSourceItem):
            raise ValueError("idea source output must contain only IdeaSourceItem values")
        if (
            not item.external_id
            or not item.title
            or not item.url
            or any(not label for label in item.labels)
        ):
            raise ValueError("idea source item fields are invalid")
        try:
            updated_at = datetime.fromisoformat(item.updated_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("idea source updated_at must be an ISO 8601 timestamp") from exc
        if updated_at.tzinfo is None:
            raise ValueError("idea source updated_at must include a time zone")
        result.append(item)
    return tuple(result)


def _is_item_sequence(value: object) -> TypeGuard[Sequence[object]]:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))
