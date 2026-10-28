"""Capture open composer ideas from a title."""

from __future__ import annotations

import re
import unicodedata

from orchestra.canon.project import Project
from orchestra.canon.store import StoreError
from orchestra.canon.validation import ValidationError


class IdeaError(Exception):
    pass


def slugify(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    if len(slug) > 60:
        slug = slug[:60].rstrip("-")
    if not slug:
        raise IdeaError("title does not produce a valid subject")
    return slug


def capture(
    project: Project,
    title: str,
    *,
    area: str | None = None,
    effort: str | None = None,
    source: str | None = None,
    body: str | None = None,
) -> dict:
    slug = slugify(title)
    try:
        project.resolve("composer:idea", slug)
    except StoreError:
        pass
    else:
        raise IdeaError(f"composer:idea already exists for subject {slug!r}")

    parts = [f"# {title}"]
    if body:
        parts.extend(["", body])
    payload: dict[str, str] = {"status": "open"}
    if area is not None:
        payload["area"] = area
    if effort is not None:
        payload["effort"] = effort
    if source is not None:
        payload["source"] = source

    try:
        return project.create(
            record_type="composer:idea",
            subject=slug,
            payload=payload,
            body="\n".join(parts),
        )
    except (StoreError, ValidationError) as exc:
        raise IdeaError(str(exc)) from exc
