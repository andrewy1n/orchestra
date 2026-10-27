from __future__ import annotations

import pytest

from orchestra.canon.query import QueryError, parse_where, resolve_path
from conftest import make_task


@pytest.fixture
def seeded(cli, project):
    for subject, level, mode, body in [
        ("web-api", 1, "fast", "serves the API\n"),
        ("web-ui", 2, "slow", "renders pages\n"),
        ("worker", 3, "fast", ""),
    ]:
        payload = {"title": subject, "level": level, "mode": mode}
        project.create(record_type="alpha:config", subject=subject, payload=payload, body=body)
    make_task(project, "t1")
    return cli


def subjects(result):
    return [r["subject"] for r in result["records"]]


def test_type_state_and_subject_filters(seeded):
    assert seeded.ok("list")["count"] == 4
    assert subjects(seeded.ok("list", "--type", "config", "--order-by", "subject")) == ["web-api", "web-ui", "worker"]
    assert subjects(seeded.ok("list", "--state", "planned")) == ["t1"]
    assert subjects(seeded.ok("list", "--subject", "web", "--order-by", "subject")) == ["web-api", "web-ui"]
    assert subjects(seeded.ok("list", "--subject", "web", "--exact-subject")) == []
    assert subjects(seeded.ok("list", "--subject", "worker", "--exact-subject")) == ["worker"]


def test_where_operators(seeded):
    assert subjects(seeded.ok("list", "--where", "payload.level=2")) == ["web-ui"]
    assert sorted(subjects(seeded.ok("list", "--type", "config", "--where", "payload.mode!=slow"))) == ["web-api", "worker"]
    assert sorted(subjects(seeded.ok("list", "--where", "payload.level=any_of:1,3"))) == ["web-api", "worker"]
    assert subjects(seeded.ok("list", "--where", "payload.mode=fast", "--where", "payload.level=3")) == ["worker"]
    assert subjects(seeded.ok("list", "--where", "subject=worker")) == ["worker"]
    assert subjects(seeded.ok("list", "--where", "lifecycle_state=planned")) == ["t1"]


def test_not_equals_does_not_match_an_unset_field(seeded):
    assert subjects(seeded.ok("list", "--where", "payload.mode!=slow", "--order-by", "subject")) == ["web-api", "worker"]


def test_where_values_are_typed(seeded):
    assert seeded.ok("list", "--where", 'payload.level="2"')["count"] == 0
    assert seeded.ok("list", "--where", "payload.level=true")["count"] == 0


def test_grep_searches_bodies_only(seeded):
    assert subjects(seeded.ok("list", "--grep", "PAGES")) == ["web-ui"]
    assert seeded.ok("list", "--grep", "nothing-like-this")["count"] == 0
    assert seeded.ok("list", "--grep", "web-api")["count"] == 0
    excerpt = seeded.ok("list", "--grep", "pages")["records"][0]
    assert excerpt["body_excerpt"] == "renders pages"


def test_summary_and_full(seeded):
    summary = seeded.ok("list", "--subject", "web-ui", "--exact-subject")["records"][0]
    assert "body" not in summary
    assert summary["body_excerpt"] == "renders pages"
    full = seeded.ok("list", "--subject", "web-ui", "--exact-subject", "--full")["records"][0]
    assert full["body"] == "renders pages\n"


def test_order_limit_fields(seeded):
    desc = seeded.ok("list", "--type", "config", "--order-by", "payload.level", "--desc", "--limit", "2", "--fields", "subject,payload.level")
    assert desc["records"] == [{"subject": "worker", "payload.level": 3}, {"subject": "web-ui", "payload.level": 2}]
    assert desc["count"] == 2
    assert subjects(seeded.ok("list", "--type", "config", "--order-by", "recorded_at", "--limit", "1")) != []


def test_time_range(seeded):
    assert seeded.ok("list", "--since", "2999-01-01T00:00:00+00:00")["count"] == 0
    assert seeded.ok("list", "--until", "2000-01-01T00:00:00+00:00")["count"] == 0
    assert seeded.ok("list", "--since", "2000-01-01T00:00:00+00:00")["count"] == 4


def test_formats(seeded):
    lines = seeded("list", "--type", "config", "--format", "ndjson", "--fields", "subject").lines
    assert sorted(line["subject"] for line in lines) == ["web-api", "web-ui", "worker"]
    table = seeded("list", "--type", "config", "--format", "table", "--fields", "subject,payload.level", "--order-by", "subject").out.splitlines()
    assert table[0].split() == ["subject", "payload.level"]
    assert table[1].split() == ["web-api", "1"]
    tsv = seeded("list", "--type", "config", "--format", "tsv", "--fields", "subject,payload.level", "--order-by", "subject").out.splitlines()
    assert tsv[0] == "subject\tpayload.level"
    assert tsv[1] == "web-api\t1"
    default = seeded("list", "--format", "table").out.splitlines()[0].split()
    assert default == ["id", "record_type", "subject", "lifecycle_state", "revision"]


def test_bad_queries_are_clean_errors(seeded):
    assert seeded("list", "--where", "level").json["error"] == "invalid_query"
    assert seeded("list", "--where", "payload=3").json["error"] == "invalid_query"
    assert seeded("list", "--grep", "(").json["error"] == "invalid_query"
    assert seeded("list", "--limit", "0").json["error"] == "invalid_query"
    assert seeded("list", "--type", "ghost").json["error"] == "unknown_type"


def test_nested_paths_walk_dicts():
    assert resolve_path({"a": {"b": 1}}, "a.b") == 1
    filters = parse_where(["payload.a.b=1"])
    assert filters == [("payload", "a.b", "eq", 1)]
    with pytest.raises(QueryError):
        parse_where(["bogus.field=1"])
