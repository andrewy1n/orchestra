"""Find installed schema modules through the `canon.schemas` entry point group."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from importlib import metadata, resources
from pathlib import Path
from typing import Any, Iterable

from orchestra.canon.schema import SchemaError, validate_module

GROUP = "canon.schemas"
PATH_ENV = "CANON_SCHEMA_PATH"


@dataclass(frozen=True)
class InstalledModule:
    namespace: str
    version: str
    source: str
    text: str
    module: dict[str, Any]


def _entry_points() -> list[Any]:
    return list(metadata.entry_points(group=GROUP))


def _read_source(entry: Any) -> tuple[str, str]:
    package = entry.value
    if ":" in package or not package:
        raise SchemaError(f"entry point {entry.name} = {package!r} must name a package")
    source = f"{package}/{entry.name}.json"
    try:
        return source, resources.files(package).joinpath(f"{entry.name}.json").read_text(
            encoding="utf-8"
        )
    except (OSError, ModuleNotFoundError, TypeError) as exc:
        raise SchemaError(f"cannot read schema module {source!r}: {exc}") from exc


def _path_sources() -> list[tuple[str, str]]:
    sources = []
    for raw in os.environ.get(PATH_ENV, "").split(os.pathsep):
        if not raw:
            continue
        try:
            sources.append((raw, Path(raw).expanduser().read_text(encoding="utf-8")))
        except OSError as exc:
            raise SchemaError(f"cannot read schema module {raw!r} from {PATH_ENV}: {exc}") from exc
    return sources


def discover() -> dict[str, InstalledModule]:
    installed = _collect(_read_source(entry) for entry in _entry_points())
    return installed | _collect(_path_sources())


def _collect(sources: Iterable[tuple[str, str]]) -> dict[str, InstalledModule]:
    found: dict[str, InstalledModule] = {}
    for source, text in sources:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise SchemaError(f"malformed JSON in schema module {source!r}: {exc}") from exc
        module = validate_module(data, source)
        installed = InstalledModule(module["namespace"], module["version"], source, text, module)
        known = found.get(installed.namespace)
        if known is not None and known.text != text:
            raise SchemaError(
                f"namespace {installed.namespace!r} is provided twice: "
                f"{known.source} and {installed.source}"
            )
        found[installed.namespace] = installed
    return found
