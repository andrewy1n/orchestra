"""Schema modules: parsing, validation, and the set of types a store accepts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from orchestra.canon.backend import Backend, open_backend
from orchestra.canon.errors import StoreError
from orchestra.canon.lifecycle import LIFECYCLES, Lifecycle
from orchestra.canon.types import JsonObject, JsonValue, get_list, get_object, get_string

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
    fields: dict[str, JsonObject]
    sections: tuple[str, ...]

    @property
    def namespace(self) -> str:
        return self.record_type.split(":", 1)[0]


def major(version: str) -> int:
    return int(version.split(".", 1)[0])


def _form_kind(form: JsonObject, where: str) -> str:
    kinds = [key for key in ("type", "enum", "ref", "list") if key in form]
    if len(kinds) != 1:
        raise SchemaError(f"{where}: a field needs exactly one of type, enum, ref, list")
    return kinds[0]


def check_form(form: JsonValue, where: str, *, top: bool) -> None:
    form_object = get_object({"form": form}, "form")
    if form_object is None:
        raise SchemaError(f"{where}: a field must be an object")
    kind = _form_kind(form_object, where)
    allowed: set[str] = {kind}
    if top:
        allowed.add("optional")
    if kind == "ref":
        allowed.add("pin")
    unknown = sorted(set(form_object) - allowed)
    if unknown:
        raise SchemaError(f"{where}: unknown keys {unknown}")
    if "optional" in form_object and not isinstance(form_object["optional"], bool):
        raise SchemaError(f"{where}: optional must be a boolean")
    if "pin" in form_object and not isinstance(form_object["pin"], bool):
        raise SchemaError(f"{where}: pin must be a boolean")
    value = form_object[kind]
    if kind == "type":
        if value not in SCALARS:
            raise SchemaError(f"{where}: type must be one of {list(SCALARS)}")
    elif kind == "enum":
        enum_values = get_list({"value": value}, "value")
        if (
            enum_values is None
            or not enum_values
            or not all(isinstance(item, str) and item for item in enum_values)
            or len(set(enum_values)) != len(enum_values)
        ):
            raise SchemaError(f"{where}: enum must be a non-empty list of distinct strings")
    elif kind == "ref":
        targets = get_list({"value": value}, "value") or [value]
        if not targets or not all(isinstance(t, str) and QUALIFIED.match(t) for t in targets):
            raise SchemaError(f"{where}: ref must be '<ns>:<type>' or a list of them")
    else:
        check_form(value, f"{where}[]", top=False)


def check_migrations(migrations: JsonValue, where: str) -> list[JsonObject]:
    migration_list = get_list({"migrations": migrations}, "migrations")
    if migration_list is None:
        raise SchemaError(f"{where}: migrations must be a list")
    for index, raw_step in enumerate(migration_list):
        label = f"{where}[{index}]"
        step = get_object({"step": raw_step}, "step")
        if step is None:
            raise SchemaError(f"{label}: a migration must be an object")
        unknown = sorted(set(step) - MIGRATION_KEYS)
        if unknown:
            raise SchemaError(f"{label}: unknown keys {unknown}")
        for key in ("from", "to"):
            version = get_string(step, key)
            if version is None or not version.isdigit():
                raise SchemaError(f"{label}: {key} must be a major version string")
        from_version = get_string(step, "from")
        to_version = get_string(step, "to")
        if from_version is None or to_version is None:
            raise SchemaError(f"{label}: from and to must be major version strings")
        if int(to_version) <= int(from_version):
            raise SchemaError(f"{label}: to must be greater than from")
        renames = step.get("rename_type", {})
        rename_types = get_object({"renames": renames}, "renames")
        if rename_types is None or not all(
            isinstance(k, str)  # pyright: ignore[reportUnnecessaryIsInstance]  # Direct callers may supply non-JSON mapping keys.
            and QUALIFIED.match(k)
            and isinstance(v, str)
            and QUALIFIED.match(v)
            for k, v in rename_types.items()
        ):
            raise SchemaError(f"{label}: rename_type maps '<ns>:<type>' to '<ns>:<type>'")
        fields = step.get("rename_field", {})
        rename_fields = get_object({"fields": fields}, "fields")
        if rename_fields is None or not all(
            isinstance(k, str)  # pyright: ignore[reportUnnecessaryIsInstance]  # Direct callers may supply non-JSON mapping keys.
            and QUALIFIED.match(k)
            and (field_map := get_object({"field_map": v}, "field_map")) is not None
            and all(
                isinstance(a, str)  # pyright: ignore[reportUnnecessaryIsInstance]  # Direct callers may supply non-JSON mapping keys.
                and isinstance(b, str)
                for a, b in field_map.items()
            )
            for k, v in rename_fields.items()
        ):
            raise SchemaError(f"{label}: rename_field maps a type to {{old: new}}")
        enums = step.get("map_enum", {})
        enum_maps = get_object({"enums": enums}, "enums")
        if enum_maps is None or not all(
            isinstance(k, str)  # pyright: ignore[reportUnnecessaryIsInstance]  # Direct callers may supply non-JSON mapping keys.
            and QUALIFIED.match(k.split(".", 1)[0])
            and "." in k
            and (enum_map := get_object({"enum_map": v}, "enum_map")) is not None
            and all(
                isinstance(a, str)  # pyright: ignore[reportUnnecessaryIsInstance]  # Direct callers may supply non-JSON mapping keys.
                and isinstance(b, str)
                for a, b in enum_map.items()
            )
            for k, v in enum_maps.items()
        ):
            raise SchemaError(f"{label}: map_enum maps '<type>.<field>' to {{old: new}}")
    return migration_list  # pyright: ignore[reportReturnType]  # Each migration was validated above.


def validate_module(data: JsonValue, source: str = "module") -> JsonObject:
    module = get_object({"module": data}, "module")
    if module is None:
        raise SchemaError(f"{source}: a module must be a JSON object")
    unknown = sorted(set(module) - MODULE_KEYS)
    if unknown:
        raise SchemaError(f"{source}: unknown keys {unknown}")
    namespace = get_string(module, "namespace")
    if not isinstance(namespace, str) or not NAME.match(namespace):
        raise SchemaError(f"{source}: namespace must be a lowercase slug")
    version = get_string(module, "version")
    if not isinstance(version, str) or not SEMVER.match(version):
        raise SchemaError(f"{source}: version must be MAJOR.MINOR.PATCH")
    types = get_object(module, "types")
    if types is None:
        raise SchemaError(f"{source}: types must be an object")
    for name in types:
        where = f"{source}: {namespace}:{name}"
        if not isinstance(name, str) or not NAME.match(name):  # pyright: ignore[reportUnnecessaryIsInstance]  # Direct callers may supply non-JSON mapping keys.
            raise SchemaError(f"{source}: type name {name!r} must be a lowercase slug")
        type_spec = get_object(types, name)
        if type_spec is None:
            raise SchemaError(f"{where}: a type must be an object")
        unknown = sorted(set(type_spec) - TYPE_KEYS)
        if unknown:
            raise SchemaError(f"{where}: unknown keys {unknown}")
        purpose = get_string(type_spec, "purpose")
        if purpose is None or not purpose.strip():
            raise SchemaError(f"{where}: purpose is required")
        lifecycle_value = type_spec.get("lifecycle")
        if lifecycle_value not in LIFECYCLES:  # pyright: ignore[reportArgumentType]  # Preserve TypeError for unhashable malformed lifecycle values.
            raise SchemaError(f"{where}: lifecycle must be one of {sorted(LIFECYCLES)}")
        lifecycle_name = get_string(type_spec, "lifecycle")
        if lifecycle_name is None:
            raise SchemaError(f"{where}: lifecycle must be one of {sorted(LIFECYCLES)}")
        fields = get_object(type_spec, "fields")
        if fields is None:
            raise SchemaError(f"{where}: fields is required and must be an object")
        for field, form in fields.items():
            if not isinstance(field, str) or not FIELD_NAME.match(field):  # pyright: ignore[reportUnnecessaryIsInstance]  # Direct callers may supply non-JSON mapping keys.
                raise SchemaError(f"{where}: field name {field!r} is invalid")
            if field == DEPENDS_ON and lifecycle_name == "staged":
                raise SchemaError(f"{where}: depends_on is built in for staged types")
            check_form(form, f"{where}.{field}", top=True)
        sections = get_list(type_spec, "sections")
        if "sections" in type_spec and (
            sections is None or not all(isinstance(s, str) and s for s in sections)
        ):
            raise SchemaError(f"{where}: sections must be a list of headings")
    check_migrations(module.get("migrations", []), f"{source}: migrations")
    return module


def load_module(path: Path) -> JsonObject:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SchemaError(f"cannot read schema module {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SchemaError(f"malformed JSON in schema module {path}: {exc}") from exc
    return validate_module(data, str(path))


def parse_module(text: str, source: str) -> JsonObject:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SchemaError(f"malformed JSON in schema module {source}: {exc}") from exc
    return validate_module(data, source)


def type_defs(module: JsonObject) -> dict[str, TypeDef]:
    namespace = get_string(module, "namespace")
    if namespace is None:
        raise SchemaError("module namespace must be a string")
    module_types = get_object(module, "types")
    if module_types is None:
        raise SchemaError("module types must be an object")
    defs: dict[str, TypeDef] = {}
    for name in module_types:
        spec = get_object(module_types, name)
        if spec is None:
            raise SchemaError(f"{namespace}:{name}: type must be an object")
        record_type = f"{namespace}:{name}"
        spec_fields = get_object(spec, "fields")
        purpose = get_string(spec, "purpose")
        lifecycle_name = get_string(spec, "lifecycle")
        if spec_fields is None or purpose is None or lifecycle_name is None:
            raise SchemaError(f"{record_type}: invalid type definition")
        fields: dict[str, JsonObject] = {}
        for field_name in spec_fields:
            field_form = get_object(spec_fields, field_name)
            if field_form is None:
                raise SchemaError(f"{record_type}.{field_name}: field form must be an object")
            fields[field_name] = field_form
        lifecycle = LIFECYCLES[lifecycle_name]
        if lifecycle.name == "staged":
            fields[DEPENDS_ON] = {"list": {"ref": record_type}, "optional": True}
        defs[record_type] = TypeDef(
            record_type=record_type,
            purpose=purpose,
            lifecycle=lifecycle,
            fields=fields,
            sections=tuple(
                section
                for section in (get_list(spec, "sections") or ())
                if isinstance(section, str)
            ),
        )
    return defs


def ref_targets(form: JsonObject) -> list[str]:
    value = form["ref"]
    if isinstance(value, list):
        return list(value)  # pyright: ignore[reportReturnType]  # Preserve unvalidated reference items.
    return [value]  # pyright: ignore[reportReturnType]  # Preserve unvalidated reference values.


class SchemaSet:
    """The types a store accepts, built from its snapshots."""

    def __init__(self, modules: dict[str, JsonObject]):
        self.modules = modules
        self.types: dict[str, TypeDef] = {}
        for module in modules.values():
            self.types.update(type_defs(module))

    @property
    def versions(self) -> dict[str, str]:
        versions: dict[str, str] = {}
        for namespace, module in self.modules.items():
            version = get_string(module, "version")
            if version is not None:
                versions[namespace] = version
        return versions

    @classmethod
    def load(cls, store_root: Path | Backend, config: JsonObject) -> SchemaSet:
        backend = open_backend(store_root, config) if isinstance(store_root, Path) else store_root
        schemas = get_object(config, "schemas")
        if schemas is None:
            raise SchemaError("config.json schemas must be an object")
        modules: dict[str, JsonObject] = {}
        for namespace, raw_version in schemas.items():
            version = raw_version if isinstance(raw_version, str) else None
            if version is None:
                raise SchemaError(f"{namespace}: schema version must be a string")
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

    def resolve_type(self, type_arg: object) -> str:
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
