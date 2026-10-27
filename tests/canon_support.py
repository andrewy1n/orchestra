"""Temp canon stores for the view and hook tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCHEMA_PATH = os.pathsep.join(
    [
        str(REPO / "orchestra" / "score" / "schemas" / "score.json"),
        str(REPO / "orchestra" / "conductor" / "schemas" / "conductor.json"),
        str(REPO / "orchestra" / "tuner" / "schemas" / "tuner.json"),
        str(REPO / "orchestra" / "composer" / "schemas" / "composer.json"),
    ]
)

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
os.environ["CANON_SCHEMA_PATH"] = SCHEMA_PATH

from orchestra.canon.project import open_store  # noqa: E402
from orchestra.canon.store import Store  # noqa: E402
from orchestra.canon.sync import init_store  # noqa: E402


def make_project(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    init_store(Store(root / ".canon"), ["score", "conductor", "tuner"])
    return open_store(root)


def create(project, record_type: str, subject: str, payload: dict, body: str | None = None):
    if body is None:
        sections = project.schemas().types[record_type].sections
        body = "\n\n".join(f"## {name}\n\nText." for name in sections)
    return project.create(
        record_type=record_type, subject=subject, payload=payload, body=body
    )


def seed_effort(project, effort: str = "alpha", phase: str = "p1") -> None:
    create(project, "score:effort", effort, {"goal": f"Goal of {effort}", "kind": "deliver"})
    create(
        project,
        "score:position",
        effort,
        {"position": "midway", "scope": "effort", "effort": effort},
    )
    create(
        project,
        "score:phase",
        phase,
        {"title": "Phase one", "ordinal": 1, "effort": effort},
    )


def point_effort_at(project, record_type: str, effort: str) -> None:
    from orchestra.canon.record_file import dump_record, load_record
    from orchestra.canon.revision import with_revision

    namespace, _, name = record_type.partition(":")
    path = next((project.store_path / "records" / f"{namespace}__{name}").glob("*.md"))
    record = load_record(path.read_text(), path)
    record["payload"]["effort"] = effort
    path.write_text(dump_record(with_revision(record)))
