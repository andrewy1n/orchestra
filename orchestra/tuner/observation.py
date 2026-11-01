"""Record and list technique-run observations in the artifact store."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from orchestra.canon.project import Project, open_store
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.tuner.manifest import merge_base, resolve_commit

_OBS_TYPE = "tuner:evidence-observation"


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
) -> None:
    """Best-effort record; failures go to stderr and never raise."""
    try:
        record_observation(
            cwd,
            technique=technique,
            base_rev=base_rev,
            head_rev=head_rev,
            result=result,
            claim_ids=claim_ids,
            replay=replay,
            subject=subject,
        )
    except Exception as exc:
        print(f"observation record skipped: {exc}", file=sys.stderr)


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
) -> None:
    """Best-effort record; failures go to stderr and never raise."""
    try:
        record_verdict_observation(cwd, at=at, base=base, claim_ids=claim_ids, result=result)
    except Exception as exc:
        print(f"observation record skipped: {exc}", file=sys.stderr)


def _claim_ids_of(item: Record) -> list[str]:
    raw = item.get("claim_ids") if "claim_ids" in item else item.get("payload", {}).get("claim_ids")
    if isinstance(raw, (list, tuple)):
        values: list[str] = []
        for value in raw:
            normalized: object = value
            values.append(str(normalized))
        return values
    return []


def _technique_of(item: Record) -> str | None:
    if "technique" in item:
        value = item.get("technique")
        return value if isinstance(value, str) else None
    value = item.get("payload", {}).get("technique")
    return value if isinstance(value, str) else None


def _matches_claim(item: Record, claim: str) -> bool:
    return claim in _claim_ids_of(item)


def list_observations(
    cwd: Path | str,
    *,
    claim: str | None = None,
    technique: str | None = None,
) -> list[Record]:
    """List evidence-observations from the subject store as plain dicts."""
    root = Path(cwd)
    if not store_usable(root):
        return []
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
