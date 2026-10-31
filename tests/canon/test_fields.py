from __future__ import annotations

import copy

import pytest

from orchestra.canon.schema import SchemaError, SchemaSet, validate_module
from orchestra.canon.validation import ValidationError
from conftest import ALPHA, BETA, PLAN_BODY, make_task


def config(project, **payload):
    base = {"title": "t", "level": 1}
    base.update(payload)
    return project.create(
        record_type="alpha:config", subject=f"c{len(project.records())}", payload=base
    )


def test_scalars_accept_their_type(project):
    record = config(project, ratio=1, enabled=True)
    assert record["payload"] == {"title": "t", "level": 1, "ratio": 1, "enabled": True}
    assert config(project, ratio=1.5)["payload"]["ratio"] == 1.5


@pytest.mark.parametrize(
    "payload",
    [
        {"title": 5},
        {"level": "1"},
        {"level": 1.5},
        {"level": True},
        {"ratio": "1.5"},
        {"ratio": False},
        {"enabled": "yes"},
        {"enabled": 1},
        {"tags": "a,b"},
        {"tags": ["a", 2]},
        {"title": None},
    ],
)
def test_scalars_refuse_other_types(project, payload):
    with pytest.raises(ValidationError, match="expected"):
        config(project, **payload)


def test_required_string_may_be_empty(project):
    assert config(project, title="")["payload"]["title"] == ""


def test_enum_accepts_listed_values_only(project):
    assert config(project, mode="fast")["payload"]["mode"] == "fast"
    with pytest.raises(ValidationError, match="one of"):
        config(project, mode="medium")


def test_empty_enum_needs_the_field_to_be_optional(project):
    assert config(project, mode="")["payload"]["mode"] == ""
    with pytest.raises(ValidationError, match="one of"):
        project.create(
            record_type="beta:review",
            subject="t",
            payload={"task": "", "verdict": ""},
        )


def test_list_of_scalars(project):
    assert config(project, tags=["a", "b"])["payload"]["tags"] == ["a", "b"]
    assert config(project, tags=[])["payload"]["tags"] == []


def test_unknown_payload_keys_are_refused(project):
    with pytest.raises(ValidationError, match="'colour' is not declared"):
        config(project, colour="red")


def test_unknown_payload_keys_are_refused_on_update(project):
    record = config(project)
    with pytest.raises(ValidationError, match="'colour' is not declared"):
        project.update(record["id"], payload={"colour": "red"})


def test_missing_required_field_is_refused(project):
    with pytest.raises(ValidationError, match="missing payload field 'level'"):
        project.create(record_type="alpha:config", subject="c", payload={"title": "t"})


def test_optional_fields_may_be_absent(project):
    record = project.create(
        record_type="alpha:config", subject="c", payload={"title": "t", "level": 1}
    )
    assert "ratio" not in record["payload"]


def test_payload_must_be_an_object(project):
    from orchestra.canon.errors import StoreError

    with pytest.raises(StoreError, match="JSON object"):
        project.create(record_type="alpha:config", subject="c", payload=["x"])


def test_subject_is_required_and_has_no_whitespace(project):
    from orchestra.canon.errors import StoreError

    with pytest.raises(StoreError, match="missing subject"):
        project.create(record_type="alpha:config", subject="", payload={"title": "t", "level": 1})
    with pytest.raises(ValidationError, match="slug"):
        project.create(
            record_type="alpha:config", subject="two words", payload={"title": "t", "level": 1}
        )


def test_short_type_names_resolve_when_unique(project):
    assert project.create(record_type="plan", subject="p", payload={"goal": "g"}, body=PLAN_BODY)
    assert project.list("plan")[0]["record_type"] == "beta:plan"


def test_required_sections_must_be_present_and_filled(project):
    with pytest.raises(ValidationError, match="missing required section 'Orientation'"):
        project.create(record_type="beta:plan", subject="p", payload={"goal": "g"})
    with pytest.raises(ValidationError, match="'Orientation' is empty"):
        project.create(
            record_type="beta:plan", subject="p", payload={"goal": "g"}, body="## Orientation\n"
        )
    stored = project.create(
        record_type="beta:plan", subject="p", payload={"goal": "g"}, body=PLAN_BODY
    )
    assert stored["body"] == PLAN_BODY


def test_envelope_carries_only_the_new_keys(project):
    record = make_task(project, "t")
    assert set(record) == {
        "id",
        "record_type",
        "subject",
        "lifecycle_state",
        "payload",
        "relationships",
        "recorded_at",
        "revision",
        "body",
    }
    assert record["id"].startswith("rec-")


def test_time_and_provenance_are_kept_as_written(project):
    record = project.create(
        record_type="alpha:config",
        subject="c",
        payload={"title": "t", "level": 1},
        time={"anything": [1, 2]},
        provenance="somewhere",
    )
    stored = project.get(record["id"])
    assert stored["time"] == {"anything": [1, 2]}
    assert stored["provenance"] == "somewhere"


def test_depends_on_is_a_built_in_field_of_staged_types(project):
    schemas = project.schemas()
    assert schemas.types["alpha:task"].fields["depends_on"] == {
        "list": {"ref": "alpha:task"},
        "optional": True,
    }
    assert "depends_on" not in schemas.types["alpha:log"].fields


class TestModuleValidation:
    def module(self, **changes):
        data = copy.deepcopy(ALPHA)
        data.update(changes)
        return data

    def test_fixture_modules_are_valid(self):
        validate_module(copy.deepcopy(ALPHA))
        validate_module(copy.deepcopy(BETA))

    @pytest.mark.parametrize(
        "mutate, message",
        [
            (lambda m: m.update(extra=1), "unknown keys"),
            (lambda m: m.update(namespace="Bad_Name"), "namespace"),
            (lambda m: m.update(version="1.0"), "version"),
            (lambda m: m["types"]["task"].update(extra=1), "unknown keys"),
            (lambda m: m["types"]["task"].pop("purpose"), "purpose"),
            (lambda m: m["types"]["task"].update(purpose=" "), "purpose"),
            (lambda m: m["types"]["task"].update(lifecycle="cyclic"), "lifecycle"),
            (lambda m: m["types"]["task"].pop("fields"), "fields"),
            (lambda m: m["types"]["task"].update(sections="Orientation"), "sections"),
            (
                lambda m: m["types"]["task"]["fields"].update(
                    depends_on={"list": {"type": "string"}}
                ),
                "built in",
            ),
            (
                lambda m: m["types"]["task"]["fields"].update(x={"type": "date"}),
                "type must be one of",
            ),
            (lambda m: m["types"]["task"]["fields"].update(x={"enum": []}), "enum"),
            (lambda m: m["types"]["task"]["fields"].update(x={"enum": ["a", "a"]}), "enum"),
            (lambda m: m["types"]["task"]["fields"].update(x={"ref": "task"}), "ref must be"),
            (
                lambda m: m["types"]["task"]["fields"].update(x={"type": "string", "enum": ["a"]}),
                "exactly one",
            ),
            (
                lambda m: m["types"]["task"]["fields"].update(x={"type": "string", "pin": True}),
                "unknown keys",
            ),
            (
                lambda m: m["types"]["task"]["fields"].update(
                    x={"list": {"type": "string", "optional": True}}
                ),
                "unknown keys",
            ),
            (
                lambda m: m["types"]["task"]["fields"].update(
                    x={"type": "string", "optional": "yes"}
                ),
                "optional",
            ),
            (
                lambda m: m["types"]["task"]["fields"].update({"Bad Name": {"type": "string"}}),
                "field name",
            ),
            (lambda m: m.update(migrations=[{"from": "1", "to": "1"}]), "greater"),
            (
                lambda m: m.update(migrations=[{"from": "1", "to": "2", "mystery": {}}]),
                "unknown keys",
            ),
            (
                lambda m: m.update(
                    migrations=[{"from": "1", "to": "2", "rename_type": {"a": "b"}}]
                ),
                "rename_type",
            ),
        ],
    )
    def test_invalid_module_is_refused(self, mutate, message):
        data = copy.deepcopy(ALPHA)
        mutate(data)
        with pytest.raises(SchemaError, match=message):
            validate_module(data)

    def test_a_module_may_reference_types_of_other_namespaces(self):
        validate_module(copy.deepcopy(BETA))
        SchemaSet({"beta": copy.deepcopy(BETA)})

    def test_nested_lists_are_allowed(self):
        data = copy.deepcopy(ALPHA)
        data["types"]["config"]["fields"]["grid"] = {"list": {"list": {"type": "integer"}}}
        validate_module(data)
