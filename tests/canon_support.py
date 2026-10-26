"""Temp canon stores for the view and hook tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CANON_ROOT = Path(
    os.environ.get("CANON_ROOT", "/home/andrewyin/adaptive-artifacts/.worktrees/canon")
)
AFF_SCHEMA = Path(
    "/home/andrewyin/affidavit/.worktrees/canon/affidavit/schemas/aff.json"
)
SCHEMA_PATH = os.pathsep.join(
    [
        str(REPO / "orchestra" / "schemas" / "plan.json"),
        str(REPO / "orchestra" / "schemas" / "run.json"),
        str(AFF_SCHEMA),
    ]
)

if str(CANON_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(CANON_ROOT / "src"))
os.environ["CANON_SCHEMA_PATH"] = SCHEMA_PATH

from canon.project import open_store  # noqa: E402
from canon.store import Store  # noqa: E402
from canon.sync import init_store  # noqa: E402


def make_project(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    init_store(Store(root / ".artifacts"), ["plan", "run", "aff"])
    return open_store(root)


def create(project, record_type: str, subject: str, payload: dict, body: str | None = None):
    if body is None:
        sections = project.schemas().types[record_type].sections
        body = "\n\n".join(f"## {name}\n\nText." for name in sections)
    return project.create(
        record_type=record_type, subject=subject, payload=payload, body=body
    )


def seed_effort(project, effort: str = "alpha", phase: str = "p1") -> None:
    create(project, "plan:effort", effort, {"goal": f"Goal of {effort}", "kind": "deliver"})
    create(
        project,
        "plan:position",
        effort,
        {"position": "midway", "scope": "effort", "effort": effort},
    )
    create(
        project,
        "plan:phase",
        phase,
        {"title": "Phase one", "ordinal": 1, "effort": effort},
    )


def point_effort_at(project, record_type: str, effort: str) -> None:
    from canon.record_file import dump_record, load_record
    from canon.revision import with_revision

    namespace, _, name = record_type.partition(":")
    path = next((project.store_path / "records" / f"{namespace}__{name}").glob("*.md"))
    record = load_record(path.read_text(), path)
    record["payload"]["effort"] = effort
    path.write_text(dump_record(with_revision(record)))
