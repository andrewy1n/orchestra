"""Schema modules: parsing, validation, and the set of types a store accepts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from orchestra.canon.backend import Backend, open_backend
from orchestra.canon.lifecycle import LIFECYCLES, Lifecycle
from orchestra.canon.store import StoreError

NAME = re.compile(r"^[a-z][a-z0-9-]*$")
QUALIFIED = re.compile(r"^[a-z][a-z0-9-]*:[a-z][a-z0-9-]*$")
FIELD_NAME = re.compile(r"^[a-z_][a-z0-9_]*$")
SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
MODULE_KEYS = {"namespace", "version", "types", "migrations"}
TYPE_KEYS = {"purpose", "lifecycle", "fields", "sections"}
SCALARS = ("string", "integer", "number", "boolean")
MIGRATION_KEYS = {"from", "to", "rename_type", "rename_field", "map_enum"}
DEPENDS_ON = "depends_on"


class SchemaError(StoreError):
    pass


@dataclass(frozen=True)
class TypeDef:
    record_type: str
    purpose: str
    lifecycle: Lifecycle
    fields: dict[str, dict[str, Any]]
    sections: tuple[str, ...]

    @property
    def namespace(self) -> str:
        return self.record_type.split(":", 1)[0]


def major(version: str) -> int:
    return int(version.split(".", 1)[0])


def _form_kind(form: Any, where: str) -> str:
    if not isinstance(form, dict):
        raise SchemaError(f"{where}: a field must be an object")
    kinds = [key for key in ("type", "enum", "ref", "list") if key in form]
    if len(kinds) != 1:
        raise SchemaError(f"{where}: a field needs exactly one of type, enum, ref, list")
    return kinds[0]


def check_form(form: Any, where: str, *, top: bool) -> None:
    kind = _form_kind(form, where)
    allowed = {kind} | ({"optional"} if top else set()) | ({"pin"} if kind == "ref" else set())
    unknown = sorted(set(form) - allowed)
    if unknown:
        raise SchemaError(f"{where}: unknown keys {unknown}")
    if "optional" in form and not isinstance(form["optional"], bool):
        raise SchemaError(f"{where}: optional must be a boolean")
    if "pin" in form and not isinstance(form["pin"], bool):
        raise SchemaError(f"{where}: pin must be a boolean")
    value = form[kind]
    if kind == "type":
        if value not in SCALARS:
            raise SchemaError(f"{where}: type must be one of {list(SCALARS)}")
    elif kind == "enum":
        if (
            not isinstance(value, list)
            or not value
            or not all(isinstance(item, str) and item for item in value)
            or len(set(value)) != len(value)
        ):
            raise SchemaError(f"{where}: enum must be a non-empty list of distinct strings")
    elif kind == "ref":
        targets = value if isinstance(value, list) else [value]
        if not targets or not all(isinstance(t, str) and QUALIFIED.match(t) for t in targets):
            raise SchemaError(f"{where}: ref must be '<ns>:<type>' or a list of them")
    else:
        check_form(value, f"{where}[]", top=False)


def check_migrations(migrations: Any, where: str) -> list[dict[str, Any]]:
    if not isinstance(migrations, list):
        raise SchemaError(f"{where}: migrations must be a list")
    for index, step in enumerate(migrations):
        label = f"{where}[{index}]"
        if not isinstance(step, dict):
            raise SchemaError(f"{label}: a migration must be an object")
        unknown = sorted(set(step) - MIGRATION_KEYS)
        if unknown:
            raise SchemaError(f"{label}: unknown keys {unknown}")
        for key in ("from", "to"):
            if not isinstance(step.get(key), str) or not step[key].isdigit():
                raise SchemaError(f"{label}: {key} must be a major version string")
        if int(step["to"]) <= int(step["from"]):
            raise SchemaError(f"{label}: to must be greater than from")
        renames = step.get("rename_type", {})
        if not isinstance(renames, dict) or not all(
            isinstance(k, str) and QUALIFIED.match(k) and isinstance(v, str) and QUALIFIED.match(v)
            for k, v in renames.items()
        ):
            raise SchemaError(f"{label}: rename_type maps '<ns>:<type>' to '<ns>:<type>'")
        fields = step.get("rename_field", {})
        if not isinstance(fields, dict) or not all(
            isinstance(k, str)
            and QUALIFIED.match(k)
            and isinstance(v, dict)
            and all(isinstance(a, str) and isinstance(b, str) for a, b in v.items())
            for k, v in fields.items()
        ):
            raise SchemaError(f"{label}: rename_field maps a type to {{old: new}}")
        enums = step.get("map_enum", {})
        if not isinstance(enums, dict) or not all(
            isinstance(k, str)
            and QUALIFIED.match(k.split(".", 1)[0])
            and "." in k
            and isinstance(v, dict)
            and all(isinstance(a, str) and isinstance(b, str) for a, b in v.items())
            for k, v in enums.items()
        ):
            raise SchemaError(f"{label}: map_enum maps '<type>.<field>' to {{old: new}}")
    return migrations


def validate_module(data: Any, source: str = "module") -> dict[str, Any]:
    if not isinstance(data, dict):
        raise SchemaError(f"{source}: a module must be a JSON object")
    unknown = sorted(set(data) - MODULE_KEYS)
    if unknown:
        raise SchemaError(f"{source}: unknown keys {unknown}")
    namespace = data.get("namespace")
    if not isinstance(namespace, str) or not NAME.match(namespace):
        raise SchemaError(f"{source}: namespace must be a lowercase slug")
    version = data.get("version")
    if not isinstance(version, str) or not SEMVER.match(version):
        raise SchemaError(f"{source}: version must be MAJOR.MINOR.PATCH")
    types = data.get("types")
    if not isinstance(types, dict):
        raise SchemaError(f"{source}: types must be an object")
    for name, spec in types.items():
        where = f"{source}: {namespace}:{name}"
        if not isinstance(name, str) or not NAME.match(name):
            raise SchemaError(f"{source}: type name {name!r} must be a lowercase slug")
        if not isinstance(spec, dict):
            raise SchemaError(f"{where}: a type must be an object")
        unknown = sorted(set(spec) - TYPE_KEYS)
        if unknown:
            raise SchemaError(f"{where}: unknown keys {unknown}")
        purpose = spec.get("purpose")
        if not isinstance(purpose, str) or not purpose.strip():
            raise SchemaError(f"{where}: purpose is required")
        if spec.get("lifecycle") not in LIFECYCLES:
            raise SchemaError(f"{where}: lifecycle must be one of {sorted(LIFECYCLES)}")
        fields = spec.get("fields")
        if not isinstance(fields, dict):
            raise SchemaError(f"{where}: fields is required and must be an object")
        for field, form in fields.items():
            if not isinstance(field, str) or not FIELD_NAME.match(field):
                raise SchemaError(f"{where}: field name {field!r} is invalid")
            if field == DEPENDS_ON and spec["lifecycle"] == "staged":
                raise SchemaError(f"{where}: depends_on is built in for staged types")
            check_form(form, f"{where}.{field}", top=True)
        sections = spec.get("sections", [])
        if not isinstance(sections, list) or not all(isinstance(s, str) and s for s in sections):
            raise SchemaError(f"{where}: sections must be a list of headings")
    check_migrations(data.get("migrations", []), f"{source}: migrations")
    return data


def load_module(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SchemaError(f"cannot read schema module {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SchemaError(f"malformed JSON in schema module {path}: {exc}") from exc
    return validate_module(data, str(path))


def parse_module(text: str, source: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SchemaError(f"malformed JSON in schema module {source}: {exc}") from exc
    return validate_module(data, source)


def type_defs(module: dict[str, Any]) -> dict[str, TypeDef]:
    namespace = module["namespace"]
    defs: dict[str, TypeDef] = {}
    for name, spec in module["types"].items():
        record_type = f"{namespace}:{name}"
        fields = dict(spec["fields"])
        lifecycle = LIFECYCLES[spec["lifecycle"]]
        if lifecycle.name == "staged":
            fields[DEPENDS_ON] = {"list": {"ref": record_type}, "optional": True}
        defs[record_type] = TypeDef(
            record_type=record_type,
            purpose=spec["purpose"],
            lifecycle=lifecycle,
            fields=fields,
            sections=tuple(spec.get("sections") or ()),
        )
    return defs


def ref_targets(form: dict[str, Any]) -> list[str]:
    value = form["ref"]
    return list(value) if isinstance(value, list) else [value]


class SchemaSet:
    """The types a store accepts, built from its snapshots."""

    def __init__(self, modules: dict[str, dict[str, Any]]):
        self.modules = modules
        self.types: dict[str, TypeDef] = {}
        for module in modules.values():
            self.types.update(type_defs(module))

    @property
    def versions(self) -> dict[str, str]:
        return {ns: module["version"] for ns, module in self.modules.items()}

    @classmethod
    def load(cls, store_root: Path | Backend, config: dict[str, Any]) -> "SchemaSet":
        backend = open_backend(store_root, config) if isinstance(store_root, Path) else store_root
        modules: dict[str, dict[str, Any]] = {}
        for namespace, version in config["schemas"].items():
            text = backend.read_snapshot(namespace)
            if text is None:
                raise SchemaError(
                    f"missing schema snapshot for {namespace!r}: run `canon schemas sync`"
                )
            module = parse_module(text, f"schema snapshot {namespace!r}")
            if module["namespace"] != namespace:
                raise SchemaError(f"{namespace}: snapshot namespace is {module['namespace']!r}")
            if module["version"] != version:
                raise SchemaError(
                    f"{namespace}: snapshot is {module['version']}, config.json pins {version}"
                )
            modules[namespace] = module
        return cls(modules)

    def get(self, record_type: str) -> TypeDef:
        try:
            return self.types[record_type]
        except KeyError:
            raise StoreError(f"unknown record type: {record_type!r}") from None

    def resolve_type(self, type_arg: Any) -> str:
        if not isinstance(type_arg, str) or not type_arg:
            raise StoreError(f"unknown record type: {type_arg!r}")
        if "/" in type_arg or "\\" in type_arg or type_arg in {".", ".."}:
            raise StoreError(f"unsafe record type: {type_arg!r}")
        if type_arg in self.types:
            return type_arg
        suffix = ":" + type_arg
        matches = sorted(t for t in self.types if t.endswith(suffix))
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise StoreError(f"ambiguous record type {type_arg!r}: {matches}")
        raise StoreError(f"unknown record type: {type_arg!r}")
