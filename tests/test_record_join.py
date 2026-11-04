from datetime import datetime, timezone

from orchestra.sessions.record_join import _parse, join
from orchestra.sessions.session_types import RecordMetadata, SessionFields


def at(h, m=0):
    return datetime(2026, 1, 1, h, m, tzinfo=timezone.utc)


def session(sid: str, cwd: str, start: str | None, end: str | None) -> SessionFields:
    return {
        "session_id": sid,
        "cwd": cwd,
        "branch": "",
        "start": start,
        "end": end,
        "duration_seconds": None,
        "turns": 0,
        "cost_usd": None,
        "skills": {},
    }


def record(rid: str, store: str, when: datetime) -> RecordMetadata:
    return {
        "id": rid,
        "record_type": "t",
        "subject": "s",
        "effort": None,
        "recorded_at": when,
        "lifecycle_state": "open",
        "store": store,
    }


S1 = session("s1", "/w/proj", "2026-01-01T01:00:00Z", "2026-01-01T03:00:00Z")
S2 = session("s2", "/other/proj", "2026-01-01T02:00:00Z", "2026-01-01T04:00:00Z")


def test_five_record_fixture_attaches_and_marks_overlap():
    s2 = session("s2", "/x/proj", "2026-01-01T02:00:00Z", "2026-01-01T04:00:00Z")
    records = [
        record("a", "proj", at(1, 30)),
        record("b", "proj", at(2, 30)),
        record("c", "proj", at(3, 30)),
        record("d", "proj", at(5)),
        record("e", "elsewhere", at(2, 30)),
    ]
    out = join([S1, s2], records)
    assert out["by_session"]["s1"] == {"records": ["a", "b"], "ambiguous": ["b"]}
    assert out["by_session"]["s2"] == {"records": ["b", "c"], "ambiguous": ["b"]}
    assert out["unattached"] == ["d", "e"]


def test_window_edges_are_inclusive():
    out = join([S1], [record("lo", "proj", at(1)), record("hi", "proj", at(3))])
    assert out["by_session"]["s1"]["records"] == ["lo", "hi"]
    assert out["unattached"] == []


def test_session_without_window_gets_nothing_but_stays_listed():
    s = session("s3", "/w/proj", None, "2026-01-01T03:00:00Z")
    out = join([s], [record("a", "proj", at(2))])
    assert out["by_session"]["s3"] == {"records": [], "ambiguous": []}
    assert out["unattached"] == ["a"]


def test_parse_accepts_iso_string() -> None:
    expected = at(2)
    assert _parse("2026-01-01T02:00:00Z") == expected
    assert _parse("2026-01-01T02:00:00+00:00") == expected


def test_output_holds_ids_only():
    r = record("a", "proj", at(2))
    r["record_type"] = "SECRET"
    assert "SECRET" not in repr(join([S1], [r]))
