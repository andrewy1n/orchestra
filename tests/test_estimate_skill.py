"""tasks records size and estimate_minutes on every new work-item."""

from __future__ import annotations

import re

from helpers import skill_text
from skill_extraction import extract_invocations


def _text() -> str:
    return skill_text("tasks")


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _work_item_payloads(text: str) -> list[dict]:
    return [
        inv["payload"]
        for inv in extract_invocations(text)
        if inv["subcommand"] == "create" and inv["type"] == "score:work-item" and inv["payload"]
    ]


def test_templates_leave_size_and_estimate_blank():
    for skill in ("tasks", "execute"):
        payloads = _work_item_payloads(skill_text(skill))
        for payload in payloads:
            if "size" in payload or "estimate_minutes" in payload:
                assert not re.fullmatch(r"XS|S|M|L|XL", str(payload.get("size")))
                assert type(payload.get("estimate_minutes")) is not int
    assert _work_item_payloads(_text())


def test_every_work_item_records_size_and_estimate_minutes():
    text = _flat(_text())
    assert "Every new work-item includes `size` and `estimate_minutes`." in text
    assert (
        "`size` (`XS`|`S`|`M`|`L`|`XL`) and `estimate_minutes` (agent wall-clock, not padded)"
        in text
    )


def test_brief_bands_match_size_bands():
    assert "Guidance: XS 1–2, S 2–5, M 5–10, L 10–20, XL 20–40." in _flat(_text())


def test_sitting_shape_stays_on_the_phase_body():
    text = _flat(_text())
    assert "Phase body records session shape (`one sitting` | `more than one`)" in text
