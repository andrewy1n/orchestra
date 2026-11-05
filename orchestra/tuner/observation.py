"""Record and list technique-run observations in the artifact store."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypeGuard

from orchestra.canon.project import Project, open_store
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.tuner.manifest import merge_base, resolve_commit

_OBS_TYPE = "tuner:evidence-observation"


def _is_object_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping)


def _is_value_sequence(value: object) -> TypeGuard[Sequence[object]]:
    return isinstance(value, (list, tuple))


def store_usable(cwd: Path | str) -> bool:
    """True when the subject cwd has an openable artifact store."""
    try:
        open_store(Path(cwd))
    except Exception:
        return False
    return True


def _project(root: Path) -> Project:
    try:
        return open_store(root)
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc


def record_observation(
    cwd: Path | str,
    *,
    technique: str,
    base_rev: str,
    head_rev: str,
    result: str,
    claim_ids: Sequence[str] = (),
    replay: str | None = None,
    subject: str | None = None,
) -> Record | None:
    """Create one unbound evidence-observation for a finished technique run.

    ``replay`` is optional re-invoke metadata (a JSON string is enough).
    Returns the created record dict, or None when no usable store is present.
    Raises on create failure. Does not create a binding.
    """
    root = Path(cwd)
    if not store_usable(root):
        return None
    ids = [str(item) for item in claim_ids]
    json_ids: list[JsonValue] = [item for item in ids]
    payload: JsonObject = {
        "technique": technique,
        "base_rev": base_rev,
        "head_rev": head_rev,
        "result": result,
        "claim_ids": json_ids,
    }
    if replay:
        payload["replay"] = replay
    if not subject:
        joined = ",".join(ids)
        subject = technique + ":" + joined if joined else technique
    try:
        record = _project(root).create(
            record_type=_OBS_TYPE,
            subject=subject,
            payload=payload,
        )
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc
    if not isinstance(record, dict):  # pyright: ignore[reportUnnecessaryIsInstance]  # Preserve runtime handling of malformed record returns.
        raise RuntimeError("create did not return a record")
    return record


def maybe_record_observation(
    cwd: Path | str,
    *,
    technique: str,
    base_rev: str,
    head_rev: str,
    result: str,
    claim_ids: Sequence[str] = (),
    replay: str | None = None,
    subject: str | None = None,
) -> bool:
    """Return whether the observation was stored."""
    try:
        record = record_observation(
            cwd,
            technique=technique,
            base_rev=base_rev,
            head_rev=head_rev,
            result=result,
            claim_ids=claim_ids,
            replay=replay,
            subject=subject,
        )
        return record is not None
    except Exception as exc:
        print(f"observation record skipped: {exc}", file=sys.stderr)
        return False


def record_verdict_observation(
    cwd: Path | str,
    *,
    at: str,
    base: str | None,
    claim_ids: Sequence[str],
    result: str,
) -> Record | None:
    """Create one evidence-observation for a finished verdict run.

    Returns the created record dict, or None when no usable store is present.
    Raises on create failure (caller should not flip the judge result).
    """
    root = Path(cwd)
    if not store_usable(root):
        return None
    head_rev = resolve_commit(root, at)
    base_rev = resolve_commit(root, base if base else merge_base(root, at))
    ids = list(claim_ids)
    subject = "verdict:" + ",".join(ids) if ids else "verdict"
    return record_observation(
        root,
        technique="verdict",
        base_rev=base_rev,
        head_rev=head_rev,
        result=result,
        claim_ids=ids,
        subject=subject,
    )


def maybe_record_verdict_observation(
    cwd: Path | str,
    *,
    at: str,
    base: str | None,
    claim_ids: Sequence[str],
    result: str,
) -> bool:
    """Return whether the verdict observation was stored."""
    try:
        record = record_verdict_observation(
            cwd, at=at, base=base, claim_ids=claim_ids, result=result
        )
        return record is not None
    except Exception as exc:
        print(f"observation record skipped: {exc}", file=sys.stderr)
        return False


def _claim_ids_of(item: Mapping[str, object]) -> list[str]:
    payload = item.get("payload")
    nested: object | None = None
    if _is_object_mapping(payload):
        nested = payload.get("claim_ids")
    raw = item.get("claim_ids", nested)
    if _is_value_sequence(raw):
        return [value for value in raw if isinstance(value, str)]
    return []


def _technique_of(item: Mapping[str, object]) -> str | None:
    if "technique" in item:
        value = item.get("technique")
        return value if isinstance(value, str) else None
    payload = item.get("payload")
    value: object | None = None
    if _is_object_mapping(payload):
        value = payload.get("technique")
    return value if isinstance(value, str) else None


def _matches_claim(item: Mapping[str, object], claim: str) -> bool:
    return claim in _claim_ids_of(item)


def list_observations(
    cwd: Path | str,
    *,
    claim: str | None = None,
    technique: str | None = None,
) -> list[Record]:
    """List evidence-observations from the subject store as plain dicts."""
    root = Path(cwd)
    try:
        items = list(_project(root).list(record_type=_OBS_TYPE))
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc
    if claim is not None:
        items = [row for row in items if _matches_claim(row, claim)]
    if technique is not None:
        items = [row for row in items if _technique_of(row) == technique]
    return items
