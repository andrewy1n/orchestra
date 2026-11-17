from __future__ import annotations

import json
import re
import tempfile
import uuid
from collections.abc import Callable, Mapping
from pathlib import Path

from canon_support import make_project

from orchestra.canon.backend import open_backend
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.close_batch import CloseRequestError, build_batch
from orchestra.conductor.task_close import CloseRefused
from orchestra.tools import Git
from orchestra.tuner.manifest import DEFAULT_RUNNER

RecordSource = Callable[[str], Record]
AmendmentSource = Callable[[str], list[Record]]


def _complete(record: Record, record_type: str) -> Record:
    defaults: Record = {
        "id": record["id"],
        "record_type": record_type,
        "subject": record["id"],
        "payload": {},
        "lifecycle_state": "recorded",
        "relationships": {},
        "revision": "sha256:test",
        "recorded_at": "2026-01-01T00:00:00+00:00",
        "body": "",
    }
    return {**defaults, **record, "record_type": record_type}


def _fetch(source: RecordSource | None, record_id: str, record_type: str) -> list[Record]:
    if source is None:
        return []
    try:
        return [_complete(source(record_id), record_type)]
    except LookupError:
        return []


def _referenced_ids(request: Mapping[str, object]) -> tuple[list[str], list[str]]:
    acceptance_ids: list[str] = []
    raw_ids = request.get("acceptance_ids")
    if isinstance(raw_ids, list):
        acceptance_ids = [value for value in raw_ids if isinstance(value, str)]
    check_run_ids: list[str] = []
    raw_criteria = request.get("criteria")
    if isinstance(raw_criteria, list):
        for entry in raw_criteria:
            if isinstance(entry, Mapping):
                for key in ("check_run_id", "red_check_run_id"):
                    value = entry.get(key)
                    if isinstance(value, str) and value:
                        check_run_ids.append(value)
    return acceptance_ids, check_run_ids


def project_holding(records: list[Record]) -> Project:
    project = make_project(Path(tempfile.mkdtemp(prefix="close-batch-")))
    backend = open_backend(project.store_path)
    for record in records:
        backend.create_record(record)
    return project


def store_id(name: str) -> str:
    return f"rec-{uuid.uuid5(uuid.NAMESPACE_OID, name)}"


def _swap(text: str, names: list[str], forward: bool) -> str:
    for name in sorted(names, key=len, reverse=True):
        old, new = (name, store_id(name)) if forward else (store_id(name), name)
        text = re.sub(rf"(?<![\w-]){re.escape(old)}(?![\w-])", new, text)
    return text


def _swap_json(value: object, names: list[str], forward: bool) -> object:
    return json.loads(_swap(json.dumps(value), names, forward))


def build_in_store(
    request: Mapping[str, object],
    *,
    cwd: Path | None = None,
    check_runs: RecordSource | None = None,
    acceptances: RecordSource | None = None,
    amendments: AmendmentSource | None = None,
) -> list[JsonObject]:
    """Run build_batch against a temporary store holding the records the sources return.

    Source ids are free-form names; the store holds uuid ids, and names are swapped back in
    results so assertions see the names the sources use.
    """
    acceptance_ids, check_run_ids = _referenced_ids(request)
    names = [*acceptance_ids, *check_run_ids]
    records: list[Record] = []
    for check_run_id in check_run_ids:
        records.extend(_fetch(check_runs, check_run_id, "tuner:check-run"))
    for acceptance_id in acceptance_ids:
        records.extend(_fetch(acceptances, acceptance_id, "score:acceptance"))
        if amendments is not None:
            records.extend(
                _complete(record, "tuner:oracle-amendment") for record in amendments(acceptance_id)
            )
    names = [*names, *(record["id"] for record in records if record["id"] not in names)]
    stored: dict[tuple[str, str], Record] = {}
    for record in records:
        swapped = _swap_json(record, names, True)
        assert isinstance(swapped, dict)
        stored[(record["record_type"], record["id"])] = swapped  # pyright: ignore[reportArgumentType]
    swapped_request = _swap_json(request, names, True)
    assert isinstance(swapped_request, dict)
    try:
        ops = build_batch(swapped_request, project_holding(list(stored.values())), cwd=cwd)
    except (CloseRefused, CloseRequestError) as exc:
        raise type(exc)(_swap(str(exc), names, False)) from exc
    restored = _swap_json(ops, names, False)
    assert isinstance(restored, list)
    return [JsonObject(op) for op in restored]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]


def commit_claim_manifest(repo: Path, claim_ids: tuple[str, ...]) -> None:
    git = Git(repo)
    git.run("init", "-q")
    claims = [
        {
            "id": claim_id,
            "text": "widget works",
            "tests": ["tests/test_widget.py::test_widget"],
            "oracle_hashes": {},
        }
        for claim_id in claim_ids
    ]
    toml = (
        '[verify.stages]\nphase = ["unit"]\n\n'
        f"[verify.unit]\nrunner = {json.dumps(DEFAULT_RUNNER)}\n"
    )
    (repo / "orchestra.toml").write_text(toml, encoding="utf-8")
    (repo / ".tuner").mkdir(exist_ok=True)
    (repo / ".tuner" / "manifest.json").write_text(
        json.dumps({"claims": claims, "amendments": []}), encoding="utf-8"
    )
    git.run("add", "orchestra.toml", ".tuner/manifest.json")
    result = git.run(
        "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "-m", "manifest"
    )
    assert result.returncode == 0, result.stderr
