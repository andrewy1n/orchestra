import json
from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[1]
OWN = {"plan", "run"}
NAMESPACES = {"plan", "run", "aff"}
LIFECYCLES = {"current", "staged", "event", "question", "claim"}
MODULE_KEYS = {"namespace", "version", "types", "migrations"}
TYPE_KEYS = {"purpose", "lifecycle", "fields", "sections"}
FIELD_KEYS = {"type", "enum", "ref", "list", "pin", "optional"}
SCALARS = {"string", "integer", "number", "boolean"}


def _module_paths():
    paths = {ns: WORKTREE / "orchestra" / "schemas" / f"{ns}.json" for ns in OWN}
    sibling = WORKTREE.parents[2] / "affidavit" / ".worktrees" / "canon"
    paths["aff"] = sibling / "affidavit" / "schemas" / "aff.json"
    return paths


def _load():
    return {ns: json.loads(p.read_text()) for ns, p in _module_paths().items() if p.exists()}


def _forms(field):
    yield field
    if "list" in field:
        yield from _forms(field["list"])


def _targets(field):
    for form in _forms(field):
        target = form.get("ref")
        if target is not None:
            yield from [target] if isinstance(target, str) else target


@pytest.fixture(scope="module")
def modules():
    return _load()


def test_own_modules_exist(modules):
    assert OWN <= set(modules)


def test_module_shape(modules):
    for ns, mod in modules.items():
        assert set(mod) == MODULE_KEYS
        assert mod["namespace"] == ns
        assert mod["types"]
        for name, t in mod["types"].items():
            assert set(t) <= TYPE_KEYS, name
            assert {"purpose", "lifecycle", "fields"} <= set(t), name
            assert t["purpose"], name
            assert isinstance(t["fields"], dict), name
            assert all(isinstance(s, str) for s in t.get("sections", [])), name


def test_every_lifecycle_is_built_in(modules):
    for mod in modules.values():
        for name, t in mod["types"].items():
            assert t["lifecycle"] in LIFECYCLES, name


def test_field_forms_are_valid(modules):
    for mod in modules.values():
        for tname, t in mod["types"].items():
            for fname, field in t["fields"].items():
                where = f"{tname}.{fname}"
                assert set(field) <= FIELD_KEYS, where
                forms = list(_forms(field))
                leaf = forms[-1]
                kinds = [k for k in ("type", "enum", "ref") if k in leaf]
                assert len(kinds) == 1, where
                if "type" in leaf:
                    assert leaf["type"] in SCALARS, where
                if "enum" in leaf:
                    assert leaf["enum"] and all(isinstance(v, str) for v in leaf["enum"]), where
                if "pin" in field:
                    assert "ref" in leaf, where


def test_staged_types_do_not_declare_depends_on(modules):
    for mod in modules.values():
        for name, t in mod["types"].items():
            assert "depends_on" not in t["fields"], name


def test_ref_targets_are_known_types(modules):
    known = {
        f"{ns}:{name}": mod["types"][name]
        for ns, mod in modules.items()
        for name in mod["types"]
    }
    for mod in modules.values():
        for tname, t in mod["types"].items():
            for fname, field in t["fields"].items():
                for target in _targets(field):
                    ns, _, typ = target.partition(":")
                    assert ns in NAMESPACES, f"{tname}.{fname} -> {target}"
                    if ns in modules:
                        assert target in known, f"{tname}.{fname} -> {target}"


def test_sibling_modules_are_checked_when_present(modules):
    if NAMESPACES - set(modules):
        pytest.skip("sibling affidavit worktree absent")
