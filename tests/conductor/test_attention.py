from __future__ import annotations

import itertools

from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.attention import LandingFact, attention_items

EFFORT = "e"
OTHER = "other"
_CLOCK = itertools.count()


def _record(
    record_type: str, subject: str, payload: JsonObject, state: str = "active", body: str = ""
) -> Record:
    n = next(_CLOCK)
    return {
        "id": f"<{record_type}:{subject}-{n}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": f"r{n}",
        "recorded_at": f"2026-11-01T00:{n // 60:02d}:{n % 60:02d}Z",
        "derived": {"write_order": n},
        "body": body,
    }


def _phase(slug: str, ordinal: int, state: str, effort: str = EFFORT) -> Record:
    return _record(
        "score:phase", slug, {"title": slug, "ordinal": ordinal, "effort": effort}, state
    )


def _records(effort: str) -> list[Record]:
    p1, p2 = f"{effort}-p1", f"{effort}-p2"
    acceptance = _record(
        "score:acceptance",
        "manual-a",
        {
            "phase": p1,
            "effort": effort,
            "requirement": "R1",
            "method": "manual",
            "criterion": "looks right",
            "verify_command": "true",
        },
    )
    return [
        _phase(p1, 1, "in_progress", effort),
        _phase(p2, 2, "done", effort),
        _record("score:specification", p1, {"phase": p1, "effort": effort, "requirements": ["R1"]}),
        _record(
            "score:continuity-question", effort, {"scope": "blocker", "blocking": True}, "open"
        ),
        _record("score:continuity-question", effort, {"scope": "loose end"}, "open"),
        _record(
            "tuner:finding",
            "f1",
            {"effort": effort, "needs": "human", "claim": "decide"},
            "asserted",
        ),
        acceptance,
        _record(
            "tuner:check-run",
            "manual-a",
            {
                "effort": effort,
                "criterion_id": acceptance["id"],
                "method": "manual",
                "result": "pass",
                "signed_by": "",
                "revision": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678",
            },
            "recorded",
        ),
        _record(
            "conductor:assessment",
            p1,
            {
                "effort": effort,
                "phase": p1,
                "requirement": "R1",
                "status": "blocked",
                "next": "design",
            },
        ),
        _record(
            "conductor:integration-report",
            p1,
            {"effort": effort, "phase": p1, "result": "fail"},
        ),
    ]


def test_attention_lists_all_seven_kinds() -> None:
    records = [*_records(EFFORT), *_records(OTHER)]
    landing = {"e-p2": LandingFact(exists=True, merged=False, branch="phase/p2", ahead=3)}

    items = attention_items(records, EFFORT, landing)

    assert [item.kind for item in items] == [
        "blocking-question",
        "loop-route",
        "integration",
        "merge-branch",
        "needs-human",
        "unsigned-check",
        "open-question",
    ]
    merge = items[3]
    assert (merge.subject, merge.text, merge.body) == ("e-p2", "phase/p2", "3 ahead")
    assert items[1].next == "design"
