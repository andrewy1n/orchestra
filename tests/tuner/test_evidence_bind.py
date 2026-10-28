"""Evidence-bind oracles: explicit bindings earn claims (R1–R7).

CLI the oracles call (same `--cwd` style as verdict and trail):

- `orchestra verify bind --cwd ROOT --observation ID --claim CLAIM --base REV --head REV`
- `orchestra verify unbind --cwd ROOT --id BINDING_ID`
- `orchestra verify recheck --cwd ROOT --claim CLAIM`
"""

from __future__ import annotations

import itertools
import json
import os
import subprocess
from pathlib import Path

from conftest import run_cli
from test_verdict import (
    VERIFY,
    ALLOW,
    APP_GREEN,
    APP_RED,
    CLAIM,
    ORACLE,
    _commit,
    _git,
    _manifest,
    _payload,
    _write_tree,
)

OBS_TYPE = "tuner:evidence-observation"
BINDING_TYPE = "tuner:evidence-binding"
REQUIRED_PAYLOAD = ("observation_id", "claim_id", "base_rev", "head_rev")
_INACTIVE = frozenset(
    {"retired", "superseded", "inactive", "unbound", "withdrawn"}
)
_SEQ = itertools.count(1)


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
    base = _commit(root, "evidence-bind red")
    _write_tree(
        root,
        oracle=ORACLE,
        app=APP_GREEN,
        allowlist=ALLOW,
        manifest=_manifest(ORACLE),
    )
    head = _commit(root, "evidence-bind green")
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


def _list_typed(root: Path, record_type: str) -> subprocess.CompletedProcess[str]:
    return run_cli(
        "list",
        "--type",
        record_type,
        "--format",
        "json",
        root=root,
    )


def _records(result: subprocess.CompletedProcess[str]) -> list[dict]:
    if result.returncode != 0 or not result.stdout.strip():
        return []
    body = json.loads(result.stdout)
    return list(body.get("records") or [])


def _list_evidence_observations(root: Path) -> list[dict]:
    return _records(_list_typed(root, OBS_TYPE))


def _list_bindings(root: Path) -> list[dict]:
    result = _list_typed(root, BINDING_TYPE)
    assert result.returncode == 0, result.stdout + result.stderr
    return _records(result)


def _record_from(stdout: str) -> dict:
    body = json.loads(stdout)
    if isinstance(body, dict) and isinstance(body.get("record"), dict):
        return body["record"]
    return body


def _get_record(root: Path, record_type: str, record_id: str) -> dict:
    result = run_cli(
        "get",
        "--type",
        record_type,
        "--id",
        record_id,
        root=root,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return _record_from(result.stdout)


def _create_observation(
    root: Path, *, base: str, head: str, result: str = "pass"
) -> dict:
    create = run_cli(
        "create",
        "--type",
        OBS_TYPE,
        "--subject",
        f"oracle-bind-obs-{next(_SEQ)}",
        "--payload",
        json.dumps(
            {
                "technique": "verdict",
                "base_rev": base,
                "head_rev": head,
                "result": result,
                "claim_ids": [CLAIM],
            }
        ),
        root=root,
    )
    assert create.returncode == 0, create.stdout + create.stderr
    return json.loads(create.stdout)["record"]


def _bind(
    root: Path,
    observation_id: str,
    base: str,
    head: str,
    claim: str = CLAIM,
) -> subprocess.CompletedProcess[str]:
    return _tuner(
        "bind",
        "--cwd",
        str(root),
        "--observation",
        observation_id,
        "--claim",
        claim,
        "--base",
        base,
        "--head",
        head,
    )


def _unbind(root: Path, binding_id: str) -> subprocess.CompletedProcess[str]:
    return _tuner("unbind", "--cwd", str(root), "--id", binding_id)


def _recheck(root: Path, claim: str = CLAIM) -> subprocess.CompletedProcess[str]:
    return _tuner("recheck", "--cwd", str(root), "--claim", claim)


def _links(row: dict, observation_id: str, claim_id: str) -> bool:
    payload = row.get("payload") or {}
    return (
        payload.get("observation_id") == observation_id
        and payload.get("claim_id") == claim_id
    )


def _is_active(row: dict) -> bool:
    state = str(row.get("lifecycle_state") or "").strip().lower()
    if state in _INACTIVE:
        return False
    payload = row.get("payload") or {}
    status = str(payload.get("status") or "").strip().lower()
    if status in _INACTIVE or payload.get("retired") is True:
        return False
    if payload.get("active") is False:
        return False
    return True


def _binding_for(root: Path, observation_id: str, claim_id: str = CLAIM) -> dict:
    matches = [
        row
        for row in _list_bindings(root)
        if _links(row, observation_id, claim_id) and _is_active(row)
    ]
    assert len(matches) == 1, matches
    return matches[0]


def _head(root: Path) -> str:
    return _git(root, "rev-parse", "HEAD").stdout.strip()


def _observation_id(item: dict) -> str | None:
    return item.get("id")


def test_r1_store_accepts_evidence_binding(store: Path) -> None:
    """R1: evidence-binding payload names observation, claim, and pin revisions."""
    validate = run_cli("validate", root=store)
    assert validate.returncode == 0, validate.stdout + validate.stderr

    obs = _create_observation(store, base="base", head="head")
    payload = {
        "observation_id": obs["id"],
        "claim_id": CLAIM,
        "base_rev": "base",
        "head_rev": "head",
    }
    create = run_cli(
        "create",
        "--type",
        BINDING_TYPE,
        "--subject",
        "oracle-r1-evidence-binding",
        "--payload",
        json.dumps(payload),
        root=store,
    )
    assert create.returncode == 0, create.stdout + create.stderr
    created = json.loads(create.stdout)["record"]
    assert created["record_type"] == BINDING_TYPE
    for field, value in payload.items():
        assert created["payload"][field] == value

    for field in REQUIRED_PAYLOAD:
        missing = {k: v for k, v in payload.items() if k != field}
        rejected = run_cli(
            "create",
            "--type",
            BINDING_TYPE,
            "--subject",
            f"oracle-r1-missing-{field}",
            "--payload",
            json.dumps(missing),
            root=store,
        )
        assert rejected.returncode != 0, field


def test_r2_tuner_bind_creates_evidence_binding(store: Path) -> None:
    """R2: orchestra verify bind attaches an existing observation to a claim under pins."""
    base, head = _seed_verdict_subject(store)
    obs = _create_observation(store, base=base, head=head)
    before_ids = {row["id"] for row in _records(_list_typed(store, BINDING_TYPE))}
    snapshot = dict(obs["payload"])

    proc = _bind(store, obs["id"], base, head)
    assert proc.returncode == 0, proc.stdout + proc.stderr

    created = [
        row
        for row in _list_bindings(store)
        if row["id"] not in before_ids and _links(row, obs["id"], CLAIM)
    ]
    assert len(created) == 1, created
    row = created[0]
    assert row["record_type"] == BINDING_TYPE
    assert row["payload"]["observation_id"] == obs["id"]
    assert row["payload"]["claim_id"] == CLAIM
    assert row["payload"]["base_rev"] == base
    assert row["payload"]["head_rev"] == head
    assert _is_active(row)

    fresh = _get_record(store, OBS_TYPE, obs["id"])
    assert fresh["payload"]["claim_ids"] == snapshot["claim_ids"]
    assert fresh["payload"]["result"] == snapshot["result"]
    assert fresh["payload"]["base_rev"] == snapshot["base_rev"]
    assert fresh["payload"]["head_rev"] == snapshot["head_rev"]


def test_r3_tuner_unbind_retires_evidence_binding(store: Path) -> None:
    """R3: orchestra verify unbind retires the binding so the observation no longer earns the claim."""
    base, head = _seed_verdict_subject(store)
    obs = _create_observation(store, base=base, head=head)
    bound = _bind(store, obs["id"], base, head)
    assert bound.returncode == 0, bound.stdout + bound.stderr
    binding = _binding_for(store, obs["id"])
    assert _is_active(binding)

    retired = _unbind(store, binding["id"])
    assert retired.returncode == 0, retired.stdout + retired.stderr
    got = _get_record(store, BINDING_TYPE, binding["id"])
    assert not _is_active(got), (
        "unbound evidence-binding must be retired "
        f"(lifecycle/payload); got {got.get('lifecycle_state')!r} "
        f"payload={got.get('payload')}"
    )
    active = [
        row
        for row in _list_bindings(store)
        if _links(row, obs["id"], CLAIM) and _is_active(row)
    ]
    assert active == []
    recheck = _recheck(store, CLAIM)
    assert recheck.returncode != 0, recheck.stdout + recheck.stderr


def test_r4_tuner_recheck_nonzero_when_binding_does_not_hold(store: Path) -> None:
    """R4: recheck exits 0 while pins hold, and non-zero when unbound or pins break."""
    base, head = _seed_verdict_subject(store)
    obs = _create_observation(store, base=base, head=head)
    bound = _bind(store, obs["id"], base, head)
    assert bound.returncode == 0, bound.stdout + bound.stderr

    held = _recheck(store, CLAIM)
    assert held.returncode == 0, held.stdout + held.stderr

    binding = _binding_for(store, obs["id"])
    retired = _unbind(store, binding["id"])
    assert retired.returncode == 0, retired.stdout + retired.stderr
    unbound = _recheck(store, CLAIM)
    assert unbound.returncode != 0, unbound.stdout + unbound.stderr

    assert _head(store) == head
    bad = _create_observation(store, base=base, head=base, result="pass")
    broken_bind = _bind(store, bad["id"], base, base)
    assert broken_bind.returncode == 0, broken_bind.stdout + broken_bind.stderr
    broken = _recheck(store, CLAIM)
    assert broken.returncode != 0, (
        "recheck must exit non-zero when the binding pins no longer hold "
        "(head pinned at the red revision while worktree HEAD stays green)\n"
        + broken.stdout
        + broken.stderr
    )


def test_r5_verdict_adds_observation_not_binding(store: Path) -> None:
    """R5: a passing verdict records one observation and no evidence-binding."""
    base, head = _seed_verdict_subject(store)
    before_obs = _list_evidence_observations(store)
    before_bind = _list_typed(store, BINDING_TYPE)

    proc = _verdict(store, base, head)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _payload(proc)["result"] == "pass"

    after_obs = _list_evidence_observations(store)
    assert len(after_obs) == len(before_obs) + 1, (
        f"expected one new {OBS_TYPE} after verdict; "
        f"before={len(before_obs)} after={len(after_obs)}"
    )
    assert before_bind.returncode == 0, before_bind.stdout + before_bind.stderr
    after_bind = _list_bindings(store)
    assert len(after_bind) == len(_records(before_bind)), (
        "orchestra verify verdict must not create an evidence-binding; "
        f"before={len(_records(before_bind))} after={len(after_bind)}"
    )


def test_r6_tuner_trail_lists_unbound_observations(store: Path) -> None:
    """R6: after verdict with no bind, orchestra verify trail still lists the observation."""
    base, head = _seed_verdict_subject(store)
    before = _list_evidence_observations(store)
    proc = _verdict(store, base, head)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    after = _list_evidence_observations(store)
    created = [row for row in after if row["id"] not in {r["id"] for r in before}]
    assert len(created) == 1
    obs_id = created[0]["id"]

    trail = _tuner("trail", "--cwd", str(store))
    assert trail.returncode == 0, trail.stdout + trail.stderr
    items = json.loads(trail.stdout)
    assert isinstance(items, list)
    assert obs_id in {_observation_id(item) for item in items}

    filtered = _tuner("trail", "--cwd", str(store), "--claim", CLAIM)
    assert filtered.returncode == 0, filtered.stdout + filtered.stderr
    claimed = json.loads(filtered.stdout)
    assert any(_observation_id(item) == obs_id for item in claimed)


def _bind_then_recheck(store: Path) -> None:
    base, head = _seed_verdict_subject(store)
    obs = _create_observation(store, base=base, head=head)
    before = [
        row
        for row in _records(_list_typed(store, BINDING_TYPE))
        if _links(row, obs["id"], CLAIM) and _is_active(row)
    ]
    assert before == []

    bound = _bind(store, obs["id"], base, head)
    assert bound.returncode == 0, bound.stdout + bound.stderr
    binding = _binding_for(store, obs["id"])
    assert binding["payload"]["base_rev"] == base
    assert binding["payload"]["head_rev"] == head

    recheck = _recheck(store, CLAIM)
    assert recheck.returncode == 0, recheck.stdout + recheck.stderr


def test_r7_fixture_bind_then_recheck_exits_zero(store: Path) -> None:
    """R7: unbound observation, orchestra verify bind, then orchestra verify recheck exits 0 while pins hold."""
    _bind_then_recheck(store)


def test_check_verify_evidence_bind(store: Path) -> None:
    """verify-evidence-bind: record unbound, bind, recheck exits 0."""
    _bind_then_recheck(store)
