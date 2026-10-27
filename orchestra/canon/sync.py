"""`init --schemas`, `schemas sync`, and `schemas add`."""

from __future__ import annotations

from typing import Any

from canon.config import new_config
from canon.migrate import apply_steps, migration_path, version_tuple
from canon.modules import InstalledModule, discover
from canon.schema import SchemaError, SchemaSet, load_module, major
from canon.store import Store, StoreError
from canon.validation import validate_store


def _need(installed: dict[str, InstalledModule], namespace: str) -> InstalledModule:
    module = installed.get(namespace)
    if module is None:
        known = sorted(installed) or "none"
        raise SchemaError(
            f"no installed package provides namespace {namespace!r} (installed: {known})"
        )
    return module


def init_store(
    store: Store,
    namespaces: list[str],
    installed: dict[str, InstalledModule] | None = None,
) -> dict[str, Any]:
    installed = discover() if installed is None else installed
    modules = [_need(installed, ns) for ns in namespaces]
    with store.write_lock():
        if store.config_path().is_file():
            config = store.load_config()
            missing = [ns for ns in namespaces if ns not in config["schemas"]]
            if missing:
                raise StoreError(
                    f"store already initialized without {missing}; run `canon schemas add`"
                )
            return {"status": "already_initialized", "store": str(store.root)}
        config = new_config({m.namespace: m.version for m in modules})
        store.init(config, {m.namespace: m.text for m in modules})
    return {"status": "initialized", "store": str(store.root), "schemas": config["schemas"]}


def sync_store(
    store: Store, installed: dict[str, InstalledModule] | None = None
) -> dict[str, Any]:
    installed = discover() if installed is None else installed
    with store.write_lock():
        return _sync_locked(store, installed)


def add_namespace(
    store: Store, namespace: str, installed: dict[str, InstalledModule] | None = None
) -> dict[str, Any]:
    installed = discover() if installed is None else installed
    module = _need(installed, namespace)
    with store.write_lock():
        config = store.load_config()
        if namespace not in config["schemas"]:
            config["schemas"][namespace] = module.version
            store.write_config(config)
        return _sync_locked(store, installed)


def _sync_locked(store: Store, installed: dict[str, InstalledModule]) -> dict[str, Any]:
    config = store.load_config()
    plan: list[tuple[str, InstalledModule, dict[str, Any] | None, list[dict[str, Any]]]] = []
    for namespace in config["schemas"]:
        module = _need(installed, namespace)
        snapshot = (
            load_module(store.snapshot_path(namespace))
            if store.snapshot_path(namespace).is_file()
            else None
        )
        steps: list[dict[str, Any]] = []
        if snapshot is not None:
            if version_tuple(module.version) < version_tuple(snapshot["version"]):
                raise SchemaError(
                    f"{namespace}: installed version {module.version} is older than "
                    f"the snapshot {snapshot['version']}"
                )
            if major(module.version) > major(snapshot["version"]):
                steps = migration_path(
                    module.module, major(snapshot["version"]), major(module.version)
                )
        plan.append((namespace, module, snapshot, steps))
    report: dict[str, Any] = {}
    migrated = 0
    for namespace, module, snapshot, steps in plan:
        if steps:
            migrated += apply_steps(store, steps)
        old_text = (
            store.snapshot_path(namespace).read_text(encoding="utf-8") if snapshot else None
        )
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
        config["schemas"][namespace] = module.version
    store.write_config(config)
    schemas = SchemaSet.load(store.root, config)
    errors = validate_store(schemas, store_root=store.root, immutability=not migrated)
    return {
        "status": "synced" if not errors else "invalid",
        "schemas": report,
        "migrated_records": migrated,
        "errors": errors,
    }
