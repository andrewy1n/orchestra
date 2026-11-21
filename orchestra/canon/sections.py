"""Split a record body into its `## ` sections."""

from __future__ import annotations

import re

_HEADING = re.compile(r"^## (.+?)\s*$", re.MULTILINE)


def body_sections(body: str) -> dict[str, str]:
    """Map each `## ` heading to the stripped text up to the next one; the first of a repeated heading wins."""
    headings = list(_HEADING.finditer(body))
    sections: dict[str, str] = {}
    for position, heading in enumerate(headings):
        end = headings[position + 1].start() if position + 1 < len(headings) else len(body)
        sections.setdefault(heading.group(1), body[heading.end() : end].strip())
    return sections


def body_section(body: str, name: str) -> str:
    return body_sections(body).get(name, "")


def body_section_ci(body: str, heading: str) -> str:
    collected: list[str] = []
    collecting = False
    target = heading.strip().lower()
    for line in (body or "").splitlines():
        if line.startswith("## "):
            if collecting:
                break
            collecting = line[3:].strip().lower() == target
            continue
        if collecting:
            collected.append(line)
    return "\n".join(collected).strip()
