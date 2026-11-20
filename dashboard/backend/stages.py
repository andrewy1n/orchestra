from __future__ import annotations

import threading
from collections.abc import Sequence
from pathlib import Path

from dashboard.backend import store
from dashboard.backend.landing import rev_parse_token
from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.conductor.landing import phase_place
from orchestra.conductor.phase_progress import (
    STAGES,
    PhaseProgress,
    StageState,
    assess,
    phase_facts,
    unavailable_progress,
)
from orchestra.score.lookups import current_phases
from orchestra.score.phase import read_phase
from orchestra.tools import ToolError

_OPEN_STATES = ("planned", "in_progress")
_cache_lock = threading.Lock()
_cache: dict[str, tuple[str, dict[str, PhaseProgress]]] = {}
_READ_ERRORS = (StoreError, ToolError, OSError, ValueError)


def finished_progress() -> PhaseProgress:
    return PhaseProgress(tuple(StageState(stage, "done") for stage in STAGES), None, "", ())


def assess_phases(target: Project, records: Sequence[Record]) -> dict[str, PhaseProgress]:
    found: dict[str, PhaseProgress] = {}
    for subject, record in current_phases(records).items():
        lifecycle = record["lifecycle_state"]
        if lifecycle == "done":
            found[subject] = finished_progress()
        elif lifecycle in _OPEN_STATES:
            try:
                found[subject] = assess(phase_facts(target, records, read_phase(record)))
            except _READ_ERRORS as exc:
                found[subject] = unavailable_progress(f"progress unavailable: {exc}")
    return found


def refs_fingerprint(target: Project, records: Sequence[Record]) -> str:
    refs: set[tuple[Path, str]] = set()
    for record in current_phases(records).values():
        if record["lifecycle_state"] not in _OPEN_STATES:
            continue
        try:
            place = phase_place(read_phase(record), target.project_root)
        except _READ_ERRORS:
            continue
        refs.add((place.repo, f"refs/heads/{place.branch}"))
        refs.add((place.repo, place.base))
    return "\n".join(
        f"{repo}\0{ref}\0{rev_parse_token(repo, ref) or 'missing'}" for repo, ref in sorted(refs)
    )


def load_phase_progress(target: Project, token: str) -> dict[str, PhaseProgress]:
    with store.pinned_token(token):
        records = store.catalog_records(target)
    key = str(target.store_path)
    version = f"{token}\n{refs_fingerprint(target, records)}"
    with _cache_lock:
        cached = _cache.get(key)
        if cached is not None and cached[0] == version:
            return cached[1]
        found = assess_phases(target, records)
        _cache[key] = (version, found)
        return found
