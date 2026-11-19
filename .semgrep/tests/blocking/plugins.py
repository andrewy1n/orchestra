# ruff: noqa: ERA001

import importlib
import importlib.util
from importlib import import_module
from types import ModuleType

from orchestra.canon.extensions import resolve_plugin
from orchestra.tools import CliTool


def bypass_catalog(name: str, path: str) -> None:
    # ruleid: orchestra.plugin-catalog-bypass
    importlib.import_module(name)
    # ruleid: orchestra.plugin-catalog-bypass
    import_module(name)
    # ruleid: orchestra.plugin-catalog-bypass
    importlib.import_module("external_plugin")
    # ruleid: orchestra.plugin-catalog-bypass
    __import__(name)
    # ruleid: orchestra.plugin-catalog-bypass
    importlib.util.spec_from_file_location(name, path)


def execute_loader(loader: object, module: ModuleType) -> None:
    # ruleid: orchestra.plugin-catalog-bypass
    loader.exec_module(module)


def use_catalog(plugin_id: str) -> object:
    # ok: orchestra.plugin-catalog-bypass
    registration = resolve_plugin("tuner.verify", plugin_id)
    # ok: orchestra.plugin-catalog-bypass
    return registration.load()


def normal_import() -> type[CliTool]:
    # ok: orchestra.plugin-catalog-bypass
    return CliTool
