"""Evidence-interface oracles: store-backed observations and orchestra verify trail (R1–R4)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from conftest import run_cli
from test_verdict import (
    VERIFY,
    APP_GREEN,
    APP_RED,
    CLAIM,
    ORACLE,
    _commit,
    _manifest,
    _payload,
    _write_tree,
    ALLOW,
)

RECORD_TYPE = "tuner:evidence-observation"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    return env


def _tuner(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*VERIFY, *args],
        cwd=str(cwd) if cwd else None,
        env=_env(),
        capture_output=True,
        text=True,
    )


def _seed_verdict_subject(root: Path) -> tuple[str, str]:
    """Overlay a red→green claim-widget subject onto an existing git+store root."""
    _write_tree(
        root,
        oracle=ORACLE,
        app=APP_RED,
        allowlist=ALLOW,
        manifest=_manifest(ORACLE),
    )
    base = _commit(root, "evidence-interface red")
    _write_tree(
        root,
        oracle=ORACLE,
        app=APP_GREEN,
        allowlist=ALLOW,
        manifest=_manifest(ORACLE),
    )
    head = _commit(root, "evidence-interface green")
    return base, head


def _verdict(
    root: Path, base: str, head: str
) -> subprocess.CompletedProcess[str]:
    return _tuner(
        "verdict",
        "--cwd",
        str(root),
        "--base",
        base,
        "--at",
        head,
        CLAIM,
    )


def _list_evidence_observations(root: Path) -> list[dict]:
    result = run_cli(
        "list",
        "--type",
        RECORD_TYPE,
        "--format",
        "json",
        root=root,
    )
    if result.returncode != 0:
        return []
    body = json.loads(result.stdout)
    return list(body.get("records") or [])


def _technique(item: dict) -> str | None:
    if "technique" in item:
        return item.get("technique")
    payload = item.get("payload") or {}
    return payload.get("technique")


def _observation_id(item: dict) -> str | None:
    return item.get("id")


def test_r1_store_accepts_evidence_observation(store: Path) -> None:
    """R1 / observation-contract: evidence-observation type + canon validate."""
    validate = run_cli("validate", root=store)
    assert validate.returncode == 0, validate.stdout + validate.stderr

    create = run_cli(
        "create",
        "--type",
        RECORD_TYPE,
        "--subject",
        "oracle-r1-evidence-observation",
        "--payload",
        json.dumps(
            {
                "technique": "verdict",
                "base_rev": "base",
                "head_rev": "head",
                "result": "pass",
                "claim_ids": [CLAIM],
            }
        ),
        root=store,
    )
    assert create.returncode == 0, create.stdout + create.stderr
    created = json.loads(create.stdout)["record"]
    assert created["record_type"] == RECORD_TYPE
    assert created["payload"]["technique"] == "verdict"


def test_r2_verdict_records_one_evidence_observation(store: Path) -> None:
    """R2 / observation-cli: passing orchestra verify verdict creates one evidence-observation."""
    base, head = _seed_verdict_subject(store)
    before = _list_evidence_observations(store)
    proc = _verdict(store, base, head)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _payload(proc)["result"] == "pass"

    after = _list_evidence_observations(store)
    assert len(after) == len(before) + 1, (
        f"expected one new {RECORD_TYPE} after verdict; "
        f"before={len(before)} after={len(after)}"
    )
    created = [row for row in after if row["id"] not in {r["id"] for r in before}]
    assert len(created) == 1
    row = created[0]
    assert row["record_type"] == RECORD_TYPE
    assert row["payload"]["technique"] == "verdict"
    assert CLAIM in row["payload"]["claim_ids"]


def test_r2_verdict_without_store_matches_prephase_semantics(tmp_path: Path) -> None:
    """R2 constraint: without a usable store, stdout/exit match pre-phase verdict."""
    from test_verdict import _repo

    root = tmp_path / "no-store"
    base, head = _repo(root, base_app=APP_RED, head_app=APP_GREEN)
    assert not (root / ".canon").exists()
    proc = _verdict(root, base, head)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _payload(proc) == {
        "result": "pass",
        "claims": [{"id": CLAIM, "result": "pass"}],
    }
    assert not (root / ".canon" / "records" / "tuner__evidence-observation").exists()


def test_r3_tuner_trail_lists_observations_as_json(store: Path) -> None:
    """R3 / observation-cli-trail: orchestra verify trail prints JSON; filterable by claim id."""
    proc = _tuner("trail", "--cwd", str(store))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    items = json.loads(proc.stdout)
    assert isinstance(items, list), "orchestra verify trail must print a JSON list"

    create = run_cli(
        "create",
        "--type",
        RECORD_TYPE,
        "--subject",
        "oracle-r3-trail",
        "--payload",
        json.dumps(
            {
                "technique": "verdict",
                "base_rev": "base",
                "head_rev": "head",
                "result": "pass",
                "claim_ids": [CLAIM],
            }
        ),
        root=store,
    )
    assert create.returncode == 0, create.stdout + create.stderr
    seeded = json.loads(create.stdout)["record"]

    listed = _tuner("trail", "--cwd", str(store))
    assert listed.returncode == 0, listed.stdout + listed.stderr
    items = json.loads(listed.stdout)
    assert isinstance(items, list)
    assert seeded["id"] in {_observation_id(item) for item in items}
    match = next(item for item in items if _observation_id(item) == seeded["id"])
    assert _technique(match) == "verdict"

    filtered = _tuner("trail", "--cwd", str(store), "--claim", CLAIM)
    assert filtered.returncode == 0, filtered.stdout + filtered.stderr
    claimed = json.loads(filtered.stdout)
    assert isinstance(claimed, list)
    assert any(_observation_id(item) == seeded["id"] for item in claimed)

    other = _tuner("trail", "--cwd", str(store), "--claim", "claim-does-not-exist")
    assert other.returncode == 0, other.stdout + other.stderr
    assert seeded["id"] not in {
        _observation_id(item) for item in json.loads(other.stdout)
    }


def test_r4_verdict_trail_and_subsequent_verdict_pass(store: Path) -> None:
    """R4 / verify-evidence-interface: verdict → trail → verdict still exits 0."""
    base, head = _seed_verdict_subject(store)
    before = _list_evidence_observations(store)

    first = _verdict(store, base, head)
    assert first.returncode == 0, first.stdout + first.stderr
    assert _payload(first)["result"] == "pass"

    after = _list_evidence_observations(store)
    assert len(after) == len(before) + 1
    created = [row for row in after if row["id"] not in {r["id"] for r in before}]
    assert len(created) == 1
    obs = created[0]
    assert obs["payload"]["technique"] == "verdict"

    trail = _tuner("trail", "--cwd", str(store))
    assert trail.returncode == 0, trail.stdout + trail.stderr
    items = json.loads(trail.stdout)
    assert isinstance(items, list)
    assert any(_observation_id(item) == obs["id"] for item in items)
    assert any(
        _observation_id(item) == obs["id"] and _technique(item) == "verdict"
        for item in items
    )

    second = _verdict(store, base, head)
    assert second.returncode == 0, second.stdout + second.stderr
    assert _payload(second)["result"] == "pass"
