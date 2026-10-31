"""Create, retire, and recheck evidence bindings in the artifact store."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from orchestra.canon.project import Project, open_store
from orchestra.canon.types import JsonObject, OperationResult, Record
from orchestra.tuner.manifest import ManifestError
from orchestra.tuner.observation import store_usable
from orchestra.tuner.verdict import run_verdict

_BIND_TYPE = "tuner:evidence-binding"
_INACTIVE = frozenset({"retired", "superseded", "inactive", "unbound", "withdrawn"})


class BindingError(Exception):
    """A bind, unbind, or recheck could not be completed."""


def _project(root: Path) -> Project:
    try:
        return open_store(root)
    except BindingError:
        raise
    except Exception as exc:
        raise BindingError(str(exc)) from exc


def _require_store(cwd: Path | str) -> Path:
    root = Path(cwd)
    if not store_usable(root):
        raise BindingError("no usable artifact store")
    return root


def is_active(row: Record) -> bool:
    """True when a binding still earns its claim."""
    state = str(row.get("lifecycle_state") or "").strip().lower()
    if state in _INACTIVE:
        return False
    payload = row.get("payload") or {}
    status = str(payload.get("status") or "").strip().lower()
    return not (
        status in _INACTIVE or payload.get("retired") is True or payload.get("active") is False
    )


def list_bindings(cwd: Path | str) -> list[Record]:
    """List evidence-binding records from the subject store."""
    root = Path(cwd)
    if not store_usable(root):
        return []
    try:
        return list(_project(root).list(record_type=_BIND_TYPE))
    except BindingError:
        raise
    except Exception as exc:
        raise BindingError(str(exc)) from exc


def active_for_claim(cwd: Path | str, claim: str) -> list[Record]:
    """Active bindings whose payload claim id is ``claim``."""
    matched: list[Record] = []
    for row in list_bindings(cwd):
        payload = row.get("payload") or {}
        if payload.get("claim_id") != claim:
            continue
        if is_active(row):
            matched.append(row)
    return matched


def bind_observation(
    cwd: Path | str,
    *,
    observation_id: str,
    claim_id: str,
    base_rev: str,
    head_rev: str,
) -> Record:
    """Create one evidence-binding from an existing observation under pins."""
    root = _require_store(cwd)
    payload: JsonObject = {
        "observation_id": observation_id,
        "claim_id": claim_id,
        "base_rev": base_rev,
        "head_rev": head_rev,
    }
    subject = "bind:" + observation_id + ":" + claim_id
    try:
        record = _project(root).create(
            record_type=_BIND_TYPE,
            subject=subject,
            payload=payload,
        )
    except BindingError:
        raise
    except Exception as exc:
        raise BindingError(str(exc)) from exc
    if not isinstance(record, dict):
        raise BindingError("create did not return a record")
    return record


def unbind(cwd: Path | str, binding_id: str) -> OperationResult:
    """Retire a binding.

    current-status records move to superseded only through supersede. The
    successor keeps the pins but is marked retired so it no longer earns
    the claim.
    """
    root = _require_store(cwd)
    retired: JsonObject = {"retired": True}
    try:
        results = _project(root).apply(
            [
                {
                    "op": "supersede",
                    "type": _BIND_TYPE,
                    "id": binding_id,
                    "payload": retired,
                }
            ]
        )
    except BindingError:
        raise
    except Exception as exc:
        raise BindingError(str(exc)) from exc
    body = results[0] if results else None
    if not isinstance(body, dict) or not body.get("ok"):
        detail = ""
        if isinstance(body, dict):
            detail = str(body.get("message") or body.get("error") or "")
        raise BindingError(detail or "supersede did not return a record")
    return body


def recheck(cwd: Path | str, claim: str) -> dict[str, Any]:
    """Re-judge ``claim`` under every active binding's base and head pins.

    Raises ``BindingError`` when no active binding exists. Returns the
    verdict payload; a non-pass result means the pins do not hold.
    """
    root = _require_store(cwd)
    active = active_for_claim(root, claim)
    if not active:
        raise BindingError(f"no active binding for {claim}")
    verdict: dict[str, Any] | None = None
    for row in active:
        payload = row.get("payload") or {}
        base = payload.get("base_rev")
        head = payload.get("head_rev")
        if not isinstance(base, str) or not base or not isinstance(head, str) or not head:
            raise BindingError("binding missing pins")
        try:
            verdict = run_verdict(root, head, base, [claim])
        except ManifestError:
            raise
        if verdict.get("result") != "pass":
            return verdict
    if verdict is None:
        raise BindingError(f"no active binding for {claim}")
    return verdict
