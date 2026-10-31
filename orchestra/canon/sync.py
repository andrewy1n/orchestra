"""`init --schemas`, `schemas sync`, and `schemas add`."""

from __future__ import annotations

from orchestra.canon.backend import Backend
from orchestra.canon.config import new_config
from orchestra.canon.errors import StoreError
from orchestra.canon.migrate import apply_steps, migration_path, version_tuple
from orchestra.canon.modules import InstalledModule, discover
from orchestra.canon.schema import SchemaError, SchemaSet, major, parse_module
from orchestra.canon.types import JsonObject, JsonValue, get_object, get_string
from orchestra.canon.validation import validate_store


def _need(installed: dict[str, InstalledModule], namespace: str) -> InstalledModule:
    module = installed.get(namespace)
    if module is None:
        known = sorted(installed) or "none"
        raise SchemaError(
            f"no installed package provides namespace {namespace!r} (installed: {known})"
        )
    return module


def init_store(
    store: Backend,
    namespaces: list[str],
    installed: dict[str, InstalledModule] | None = None,
) -> JsonObject:
    installed = discover() if installed is None else installed
    modules = [_need(installed, ns) for ns in namespaces]
    with store.transaction():
        if store.has_config():
            config = store.load_config()
            schemas = get_object(config, "schemas")
            if schemas is None:
                raise StoreError("store config schemas must be an object")
            missing = [ns for ns in namespaces if ns not in schemas]
            if missing:
                raise StoreError(
                    f"store already initialized without {missing}; run `canon schemas add`"
                )
            return {"status": "already_initialized", "store": str(store)}
        config = new_config({m.namespace: m.version for m in modules})
        config["backend"] = "sqlite"
        store.init(config, {m.namespace: m.text for m in modules})
    return {"status": "initialized", "store": str(store), "schemas": config["schemas"]}


def sync_store(store: Backend, installed: dict[str, InstalledModule] | None = None) -> JsonObject:
    installed = discover() if installed is None else installed
    with store.transaction():
        return _sync_locked(store, installed)


def add_namespace(
    store: Backend, namespace: str, installed: dict[str, InstalledModule] | None = None
) -> JsonObject:
    installed = discover() if installed is None else installed
    module = _need(installed, namespace)
    with store.transaction():
        config = store.load_config()
        schemas = get_object(config, "schemas")
        if schemas is None:
            raise StoreError("store config schemas must be an object")
        if namespace not in schemas:
            schemas[namespace] = module.version
            store.write_config(config)
        return _sync_locked(store, installed)


def _sync_locked(store: Backend, installed: dict[str, InstalledModule]) -> JsonObject:
    config = store.load_config()
    schemas = get_object(config, "schemas")
    if schemas is None:
        raise StoreError("store config schemas must be an object")
    plan: list[tuple[str, InstalledModule, JsonObject | None, list[JsonObject]]] = []
    for namespace in schemas:
        module = _need(installed, namespace)
        text = store.read_snapshot(namespace)
        snapshot = (
            parse_module(text, f"schema snapshot {namespace!r}") if text is not None else None
        )
        steps: list[JsonObject] = []
        if snapshot is not None:
            snapshot_version = get_string(snapshot, "version")
            if snapshot_version is None:
                raise SchemaError(f"{namespace}: snapshot version must be a string")
            if version_tuple(module.version) < version_tuple(snapshot_version):
                raise SchemaError(
                    f"{namespace}: installed version {module.version} is older than "
                    f"the snapshot {snapshot_version}"
                )
            if major(module.version) > major(snapshot_version):
                steps = migration_path(
                    module.module, major(snapshot_version), major(module.version)
                )
        plan.append((namespace, module, snapshot, steps))
    report: JsonObject = {}
    migrated = 0
    for namespace, module, snapshot, steps in plan:
        if steps:
            migrated += apply_steps(store, steps)
        old_text = store.read_snapshot(namespace) if snapshot else None
        if old_text != module.text:
            store.write_snapshot(namespace, module.text)
        if snapshot is None:
            action = "copied"
        elif steps:
            action = "migrated"
        elif old_text != module.text:
            action = "updated"
        else:
            action = "unchanged"
        report[namespace] = {
            "from": snapshot["version"] if snapshot else None,
            "to": module.version,
            "action": action,
        }
        schemas[namespace] = module.version
    store.write_config(config)
    schemas = SchemaSet.load(store, config)
    errors = validate_store(schemas, backend=store, immutability=not migrated)
    json_errors: list[JsonValue] = []
    json_errors.extend(errors)
    return {
        "status": "synced" if not errors else "invalid",
        "schemas": report,
        "migrated_records": migrated,
        "errors": json_errors,
    }
