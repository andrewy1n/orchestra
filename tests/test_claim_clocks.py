"""Close-batch claim gates: claim id, verdict, and recheck contracts.

The claim gate is driven only by the acceptance payload field ``claim``.
A non-empty claim that is listed in ``.affidavit/manifest.json`` must run
affidavit verdict at the green check-run revision and recheck for that
claim before a ``done`` close is accepted. An acceptance that cannot be
loaded, or a claim missing from the manifest, refuses the close.

These are in-process ``build_batch`` tests with injected store loaders,
mirroring the claim-gate tests in ``tests/test_close_batch.py``.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

from conftest import AFFIDAVIT_ROOT
from orchestra import close_batch

CLAIM_ID = "claim-widget"
UNKNOWN_CLAIM_ID = "claim-not-in-manifest"
GREEN_REVISION = "green-rev-abc123"
CHECK_RUN_ID = "rec-runner-cr"


def _ensure_affidavit_importable() -> None:
    """In-process close tests call affidavit; the checkout is not an installed dep."""
    root = AFFIDAVIT_ROOT
    if (root / "affidavit" / "__init__.py").is_file() and str(root) not in sys.path:
        sys.path.insert(0, str(root))


_ensure_affidavit_importable()


def _write_manifest_claim(repo: Path, claim_id: str = CLAIM_ID) -> None:
    aff_dir = repo / ".affidavit"
    aff_dir.mkdir(parents=True, exist_ok=True)
    (aff_dir / "manifest.json").write_text(
        json.dumps(
            {
                "claims": [
                    {
                        "id": claim_id,
                        "text": "widget works",
                        "tests": ["tests/test_widget.py::test_widget"],
                        "oracle_hashes": {},
                    }
                ],
                "amendments": [],
            }
        ),
        encoding="utf-8",
    )


def _patch_affidavit(monkeypatch, module_name: str, attr: str, fn) -> None:
    _ensure_affidavit_importable()
    module = importlib.import_module(module_name)
    monkeypatch.setattr(module, attr, fn)


def _request(**overrides) -> dict:
    base = {
        "subject": "task-1",
        "effort": "effort-1",
        "work_item_id": "rec-wi",
        "transition": "done",
        "execution_report_id": "rec-er",
        "acceptance_ids": ["rec-ac1"],
        "criteria": [
            {
                "criterion_id": "rec-ac1",
                "method": "check",
                "check_run_id": CHECK_RUN_ID,
                "result": "pass",
            }
        ],
        "finding": None,
    }
    base.update(overrides)
    return base


def _matching_loader(request: dict):
    """Echo request-carried check-run fields as store records (unit-test hook)."""
    by_id: dict[str, dict] = {}
    for entry in request.get("criteria", []):
        cid = entry.get("check_run_id")
        if cid:
            payload = {
                "criterion_id": entry["criterion_id"],
                "result": entry.get("result"),
                "runner": entry.get("runner", "orchestra"),
                "revision": entry.get("revision", "deadbeef"),
                "method": entry.get("method"),
            }
            by_id[cid] = {"id": cid, "payload": payload}

    def load(check_run_id: str) -> dict:
        if check_run_id not in by_id:
            raise LookupError(check_run_id)
        return by_id[check_run_id]

    return load


def _green_loader(revision: str = GREEN_REVISION):
    """Store loader whose green check-run carries the given revision."""

    def load(check_run_id: str) -> dict:
        if check_run_id != CHECK_RUN_ID:
            raise LookupError(check_run_id)
        return {
            "id": check_run_id,
            "payload": {
                "criterion_id": "rec-ac1",
                "result": "pass",
                "runner": "orchestra",
                "revision": revision,
                "method": "check",
            },
        }

    return load


def _build(request: dict, *, cwd: Path | None = None, load_check_run=None, **kwargs):
    """build_batch with a matching store loader unless one is supplied."""
    loader = load_check_run
    if loader is None and request.get("transition") == "done":
        loader = _matching_loader(request)
    return close_batch.build_batch(
        request, cwd=cwd, load_check_run=loader, **kwargs
    )


def _acceptance(*, claim=None, include_claim: bool = True, subject: str = CLAIM_ID) -> dict:
    payload: dict = {"method": "check", "effort": "effort-1"}
    if include_claim:
        payload["claim"] = claim
    return {"id": "rec-ac1", "subject": subject, "payload": payload}


def _refusal(build) -> close_batch.CloseRefused | None:
    """Run ``build`` and return the refusal, or None when it was accepted."""
    try:
        build()
    except close_batch.CloseRefused as exc:
        return exc
    return None


# -- R1/R2: the claim id is read only from payload.claim -------------------


def test_claim_id_read_only_from_payload_claim(tmp_path, monkeypatch):
    """R1: a manifest claim named only by the acceptance subject is not gated."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_manifest_claim(repo)
    verdict_calls: list[tuple] = []
    recheck_calls: list[tuple] = []

    def run_verdict(*args, **kwargs):
        verdict_calls.append((args, kwargs))
        return {"result": "fail"}

    def recheck(*args, **kwargs):
        recheck_calls.append((args, kwargs))
        return {"result": "pass"}

    _patch_affidavit(monkeypatch, "affidavit.verdict", "run_verdict", run_verdict)
    _patch_affidavit(monkeypatch, "affidavit.binding", "recheck", recheck)

    refused = _refusal(
        lambda: _build(
            _request(),
            cwd=repo,
            load_acceptance=lambda _aid: _acceptance(
                include_claim=False, subject=CLAIM_ID
            ),
        )
    )
    assert refused is None, (
        "a claim id read only from the acceptance subject must not gate: "
        f"{refused}"
    )
    ops = _build(
        _request(),
        cwd=repo,
        load_acceptance=lambda _aid: _acceptance(
            include_claim=False, subject=CLAIM_ID
        ),
    )
    assert ops[-1]["transition"] == "done"
    assert verdict_calls == [], "verdict must not run without payload.claim"
    assert recheck_calls == [], "recheck must not run without payload.claim"


def test_empty_claim_is_not_gated(tmp_path, monkeypatch):
    """R2: payload.claim == '' is not a claim, even when subject names one."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_manifest_claim(repo)
    verdict_calls: list[tuple] = []
    recheck_calls: list[tuple] = []

    def run_verdict(*args, **kwargs):
        verdict_calls.append((args, kwargs))
        return {"result": "fail"}

    def recheck(*args, **kwargs):
        recheck_calls.append((args, kwargs))
        return {"result": "pass"}

    _patch_affidavit(monkeypatch, "affidavit.verdict", "run_verdict", run_verdict)
    _patch_affidavit(monkeypatch, "affidavit.binding", "recheck", recheck)

    refused = _refusal(
        lambda: _build(
            _request(),
            cwd=repo,
            load_acceptance=lambda _aid: _acceptance(
                claim="", subject=CLAIM_ID
            ),
        )
    )
    assert refused is None, (
        f"an empty payload.claim must not gate the close: {refused}"
    )
    ops = _build(
        _request(),
        cwd=repo,
        load_acceptance=lambda _aid: _acceptance(claim="", subject=CLAIM_ID),
    )
    assert ops[-1]["transition"] == "done"
    assert verdict_calls == [], "verdict must not run for an empty claim"
    assert recheck_calls == [], "recheck must not run for an empty claim"


# -- R3/R4: verdict at the green revision, recheck for the claim ----------


def test_verdict_runs_at_green_revision(tmp_path, monkeypatch):
    """R3: verdict is called at the green check-run revision for [claim]."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_manifest_claim(repo)
    calls: list[tuple[tuple, dict]] = []

    def run_verdict(*args, **kwargs):
        calls.append((args, kwargs))
        return {"result": "pass"}

    _patch_affidavit(monkeypatch, "affidavit.verdict", "run_verdict", run_verdict)
    _patch_affidavit(
        monkeypatch,
        "affidavit.binding",
        "recheck",
        lambda *args, **kwargs: {"result": "pass"},
    )

    ops = _build(
        _request(),
        cwd=repo,
        load_check_run=_green_loader(),
        load_acceptance=lambda _aid: _acceptance(claim=CLAIM_ID),
    )
    assert ops[-1]["transition"] == "done"
    assert calls, "run_verdict was not called for a manifest claim"
    args, _kwargs = calls[0]
    assert args[0] == repo
    assert args[1] == GREEN_REVISION
    assert args[3] == [CLAIM_ID]


def test_recheck_runs_for_claim(tmp_path, monkeypatch):
    """R4: recheck is called with the accepted claim id."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_manifest_claim(repo)
    calls: list[tuple[tuple, dict]] = []

    def recheck(*args, **kwargs):
        calls.append((args, kwargs))
        return {"result": "pass"}

    _patch_affidavit(
        monkeypatch,
        "affidavit.verdict",
        "run_verdict",
        lambda *args, **kwargs: {"result": "pass"},
    )
    _patch_affidavit(monkeypatch, "affidavit.binding", "recheck", recheck)

    ops = _build(
        _request(),
        cwd=repo,
        load_acceptance=lambda _aid: _acceptance(claim=CLAIM_ID),
    )
    assert ops[-1]["transition"] == "done"
    assert calls, "recheck was not called for a manifest claim"
    args, _kwargs = calls[0]
    assert args[0] == repo
    assert args[1] == CLAIM_ID


# -- R5/R6/R7: refusal messages name the failing gate(s) ------------------


def test_verdict_only_failure_names_verdict(tmp_path, monkeypatch):
    """R5: verdict fails and recheck passes; the refusal names verdict."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_manifest_claim(repo)
    _patch_affidavit(
        monkeypatch,
        "affidavit.verdict",
        "run_verdict",
        lambda *args, **kwargs: {"result": "fail"},
    )
    _patch_affidavit(
        monkeypatch,
        "affidavit.binding",
        "recheck",
        lambda *args, **kwargs: {"result": "pass"},
    )

    refused = _refusal(
        lambda: _build(
            _request(),
            cwd=repo,
            load_acceptance=lambda _aid: _acceptance(claim=CLAIM_ID),
        )
    )
    assert refused is not None, "verdict failure must refuse the close"
    assert "verdict" in str(refused).lower()


def test_recheck_only_failure_names_recheck(tmp_path, monkeypatch):
    """R6: verdict passes and recheck fails; the refusal names recheck."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_manifest_claim(repo)
    _patch_affidavit(
        monkeypatch,
        "affidavit.verdict",
        "run_verdict",
        lambda *args, **kwargs: {"result": "pass"},
    )
    _patch_affidavit(
        monkeypatch,
        "affidavit.binding",
        "recheck",
        lambda *args, **kwargs: {"result": "fail"},
    )

    refused = _refusal(
        lambda: _build(
            _request(),
            cwd=repo,
            load_acceptance=lambda _aid: _acceptance(claim=CLAIM_ID),
        )
    )
    assert refused is not None, "recheck failure must refuse the close"
    assert "recheck" in str(refused).lower()


def test_both_failures_name_both(tmp_path, monkeypatch):
    """R7: both gates fail; the refusal names verdict and recheck."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_manifest_claim(repo)
    _patch_affidavit(
        monkeypatch,
        "affidavit.verdict",
        "run_verdict",
        lambda *args, **kwargs: {"result": "fail"},
    )
    _patch_affidavit(
        monkeypatch,
        "affidavit.binding",
        "recheck",
        lambda *args, **kwargs: {"result": "fail"},
    )

    refused = _refusal(
        lambda: _build(
            _request(),
            cwd=repo,
            load_acceptance=lambda _aid: _acceptance(claim=CLAIM_ID),
        )
    )
    assert refused is not None, "two failing gates must refuse the close"
    msg = str(refused).lower()
    assert "verdict" in msg
    assert "recheck" in msg


# -- R8/R9: unloadable acceptance and unknown claim both refuse ----------


def test_missing_acceptance_refuses(tmp_path, monkeypatch):
    """R8: an acceptance that cannot be loaded refuses the close."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_manifest_claim(repo)

    def missing(_acceptance_id: str) -> dict:
        raise LookupError(_acceptance_id)

    refused = _refusal(
        lambda: _build(_request(), cwd=repo, load_acceptance=missing)
    )
    assert refused is not None, (
        "a close whose acceptance cannot be loaded must refuse"
    )


def test_unknown_claim_refuses(tmp_path, monkeypatch):
    """R9: a payload.claim absent from the manifest refuses the close."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_manifest_claim(repo)
    _patch_affidavit(
        monkeypatch,
        "affidavit.verdict",
        "run_verdict",
        lambda *args, **kwargs: {"result": "pass"},
    )
    _patch_affidavit(
        monkeypatch,
        "affidavit.binding",
        "recheck",
        lambda *args, **kwargs: {"result": "pass"},
    )

    refused = _refusal(
        lambda: _build(
            _request(),
            cwd=repo,
            load_acceptance=lambda _aid: _acceptance(claim=UNKNOWN_CLAIM_ID),
        )
    )
    assert refused is not None, (
        f"claim {UNKNOWN_CLAIM_ID!r} is not in the manifest and must refuse"
    )
