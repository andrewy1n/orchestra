"""plan-phase records size and estimate_minutes on every new work-item."""

from __future__ import annotations

import re

from helpers import skill_text
from skill_extraction import extract_invocations

SIZES = {"XS", "S", "M", "L", "XL"}


def _text() -> str:
    return skill_text("plan-phase")


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _work_item_payloads(text: str) -> list[dict]:
    return [
        inv["payload"]
        for inv in extract_invocations(text)
        if inv["subcommand"] == "create" and inv["type"] == "score:work-item" and inv["payload"]
    ]


def test_write_size_and_estimate_minutes_on_every_work_item():
    raw = _text()
    text = _flat(raw)
    payloads = _work_item_payloads(raw)
    assert payloads
    for payload in payloads:
        assert payload["size"] in SIZES
        minutes = payload["estimate_minutes"]
        assert type(minutes) is int
        assert 0 <= minutes < 25
    assert "Every new work-item includes `size` and `estimate_minutes`." in text
    assert (
        "`size` (`XS`|`S`|`M`|`L`|`XL`) and `estimate_minutes` (agent wall-clock, not padded)"
        in text
    )
    assert "Guidance: XS 2–5, S 5–10, M 8–15, L 15–25, XL 25–40." in text


def test_sitting_shape_stays_on_the_phase_body():
    text = _flat(_text())
    assert "Phase body records session shape (`one sitting` | `more than one`)" in text
