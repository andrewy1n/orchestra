"""Evidence-technique-ingest oracles: audit and probes record unbound observations (R1–R7).

Technique ids are ``audit`` and ``probes``. Replay metadata lives on
``payload.replay`` or the record body and must name the same revisions.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from conftest import run_cli
from test_verdict import AFF, _commit, _init

OBS_TYPE = "aff:evidence-observation"
BINDING_TYPE = "aff:evidence-binding"
AUDIT_TECHNIQUE = "audit"
PROBES_TECHNIQUE = "probes"
PROBE_ID = "value-print"
ADVISORY_KEYS = {
    "advisory",
    "base",
    "head",
    "blocks",
    "mutants",
    "survivors",
    "diffs",
}
PYTEST_INI = "[pytest]\npythonpath = .\n"
BASE_APP = "VALUE = 1\n"
HEAD_APP = "VALUE = 2\n"
PROBE_CLI = {
    "probes": [
        {
            "id": PROBE_ID,
            "kind": "cli",
            "argv": ["python3", "-c", "from app import VALUE; print(VALUE)"],
            "claims": [],
        }
    ]
}


def _env() -> dict[str, str]:
    env = os.environ.copy()
    return env


def _aff(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(AFF), *args],
        cwd=str(cwd) if cwd else None,
        env=_env(),
        capture_output=True,
        text=True,
        timeout=120,
    )


def _write(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _seed_subject(root: Path, *, probes: bool) -> tuple[str, str]:
    """Commit a one-line source change; optionally declare an unclaimed probe."""
    files = {"pytest.ini": PYTEST_INI, "app.py": BASE_APP}
    if probes:
        files[".affidavit/probes.json"] = json.dumps(PROBE_CLI, indent=2) + "\n"
    _write(root, files)
    base = _commit(root, "technique-ingest base")
    _write(root, {"app.py": HEAD_APP})
    head = _commit(root, "technique-ingest head")
    return base, head


def _audit(root: Path, base: str, head: str) -> subprocess.CompletedProcess[str]:
    return _aff("audit", "--cwd", str(root), "--base", base, "--head", head)


def _advisory(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert isinstance(payload, dict)
    assert payload.get("advisory") is True
    assert set(payload) == ADVISORY_KEYS
    return payload


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


def _list_observations(root: Path) -> list[dict]:
    return _records(_list_typed(root, OBS_TYPE))


def _list_bindings(root: Path) -> list[dict]:
    result = _list_typed(root, BINDING_TYPE)
    assert result.returncode == 0, result.stdout + result.stderr
    return _records(result)


def _created(before: list[dict], after: list[dict]) -> list[dict]:
    known = {row["id"] for row in before}
    return [row for row in after if row["id"] not in known]


def _technique(item: dict) -> str | None:
    if "technique" in item:
        return item.get("technique")
    payload = item.get("payload") or {}
    return payload.get("technique")


def _observation_id(item: dict) -> str | None:
    return item.get("id")


def _payload(item: dict) -> dict:
    payload = item.get("payload")
    return payload if isinstance(payload, dict) else {}


def _replay_text(item: dict) -> str:
    """Serialize payload.replay and/or body — the re-invoke metadata."""
    chunks: list[str] = []
    body = item.get("body")
    if isinstance(body, str) and body.strip():
        chunks.append(body)
    payload = _payload(item)
    for source in (item.get("replay"), payload.get("replay")):
        if isinstance(source, str) and source.strip():
            chunks.append(source)
        elif isinstance(source, (dict, list)) and source:
            chunks.append(json.dumps(source, sort_keys=True))
    return "\n".join(chunks)


def _of_technique(rows: list[dict], technique: str) -> list[dict]:
    return [row for row in rows if _technique(row) == technique]


def _covers_probe(row: dict, probe_id: str) -> bool:
    blob = json.dumps(_payload(row), sort_keys=True) + "\n" + str(row.get("body") or "")
    return probe_id in blob


def _assert_replay(row: dict, base: str, head: str, *needles: str) -> None:
    payload = _payload(row)
    assert payload.get("base_rev") == base, payload
    assert payload.get("head_rev") == head, payload
    assert "result" in payload, payload
    text = _replay_text(row)
    assert text.strip(), (
        f"{row.get('id')} missing replay metadata (payload.replay or body)"
    )
    assert base in text and head in text, (
        "replay metadata must name the same revisions so the technique "
        f"can be re-invoked; got {text[:500]}"
    )
    for needle in needles:
        assert needle in text, (
            f"replay metadata must identify {needle!r} to re-invoke; got {text[:500]}"
        )


def _bound_observation_ids(root: Path) -> set[str]:
    found: set[str] = set()
    for row in _list_bindings(root):
        obs = _payload(row).get("observation_id")
        if isinstance(obs, str) and obs:
            found.add(obs)
    return found


def _trail(root: Path, *args: str) -> list[dict]:
    proc = _aff("trail", "--cwd", str(root), *args)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    items = json.loads(proc.stdout)
    assert isinstance(items, list)
    return items


def test_r1_audit_records_evidence_observation(store: Path) -> None:
    """R1: aff audit with a usable store creates an audit evidence-observation."""
    base, head = _seed_subject(store, probes=False)
    before = _list_observations(store)
    proc = _audit(store, base, head)
    payload = _advisory(proc)
    assert payload["base"] == base
    assert payload["head"] == head

    created = _created(before, _list_observations(store))
    audit_rows = _of_technique(created, AUDIT_TECHNIQUE)
    assert audit_rows, (
        f"expected at least one new {OBS_TYPE} with technique {AUDIT_TECHNIQUE!r}; "
        f"created={created}"
    )
    assert all(row["record_type"] == OBS_TYPE for row in audit_rows)


def test_r2_probe_outcomes_covered_by_probe_observations(store: Path) -> None:
    """R2: each reported probe outcome is covered by a probes evidence-observation."""
    base, head = _seed_subject(store, probes=True)
    before = _list_observations(store)
    proc = _audit(store, base, head)
    payload = _advisory(proc)
    reported = [
        diff["probe"]
        for diff in payload["diffs"]
        if isinstance(diff, dict) and diff.get("probe")
    ]
    assert PROBE_ID in reported, payload["diffs"]

    created = _created(before, _list_observations(store))
    probe_rows = _of_technique(created, PROBES_TECHNIQUE)
    assert probe_rows, (
        f"expected {OBS_TYPE} with technique {PROBES_TECHNIQUE!r} "
        f"covering reported probes {reported}; created={created}"
    )
    for probe_id in reported:
        assert any(_covers_probe(row, probe_id) for row in probe_rows), (
            f"probe {probe_id!r} outcome is not covered by a "
            f"{PROBES_TECHNIQUE!r} observation"
        )


def test_r3_observations_include_replay_metadata(store: Path) -> None:
    """R3: audit and probe observations carry replay metadata for the same revisions."""
    base, head = _seed_subject(store, probes=True)
    before = _list_observations(store)
    proc = _audit(store, base, head)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    created = _created(before, _list_observations(store))
    audit_rows = _of_technique(created, AUDIT_TECHNIQUE)
    probe_rows = _of_technique(created, PROBES_TECHNIQUE)
    assert audit_rows, created
    assert probe_rows, created
    for row in audit_rows:
        _assert_replay(row, base, head, AUDIT_TECHNIQUE)
    for row in probe_rows:
        _assert_replay(row, base, head, PROBE_ID)


def test_r4_audit_creates_no_evidence_binding(store: Path) -> None:
    """R4: audit and probe recording create no evidence-binding records."""
    base, head = _seed_subject(store, probes=True)
    before = _list_bindings(store)
    before_ids = {row["id"] for row in before}
    proc = _audit(store, base, head)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    after = _list_bindings(store)
    assert len(after) == len(before), (
        "aff audit must not create an evidence-binding; "
        f"before={len(before)} after={len(after)}"
    )
    assert {row["id"] for row in after} == before_ids


def test_r5_trail_technique_filters_audit_and_probes(store: Path) -> None:
    """R5: aff trail --technique restricts the list to audit and probes ids."""
    base, head = _seed_subject(store, probes=True)
    before = _list_observations(store)
    proc = _audit(store, base, head)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    created = _created(before, _list_observations(store))
    audit_ids = {row["id"] for row in _of_technique(created, AUDIT_TECHNIQUE)}
    probe_ids = {row["id"] for row in _of_technique(created, PROBES_TECHNIQUE)}
    assert audit_ids, created
    assert probe_ids, created

    audited = _trail(store, "--technique", AUDIT_TECHNIQUE)
    audited_ids = {_observation_id(item) for item in audited}
    assert audit_ids <= audited_ids
    assert not (probe_ids & audited_ids)
    assert all(_technique(item) == AUDIT_TECHNIQUE for item in audited)

    probed = _trail(store, "--technique", PROBES_TECHNIQUE)
    probed_ids = {_observation_id(item) for item in probed}
    assert probe_ids <= probed_ids
    assert not (audit_ids & probed_ids)
    assert all(_technique(item) == PROBES_TECHNIQUE for item in probed)

    other = _trail(store, "--technique", "not-a-technique")
    other_ids = {_observation_id(item) for item in other}
    assert not (audit_ids & other_ids)
    assert not (probe_ids & other_ids)


def test_r6_audit_without_store_matches_prephase(tmp_path: Path) -> None:
    """R6: without a usable store, aff audit stays advisory JSON and exits 0."""
    root = tmp_path / "no-store"
    _init(root)
    base, head = _seed_subject(root, probes=True)
    assert not (root / ".artifacts").exists()
    proc = _audit(root, base, head)
    payload = _advisory(proc)
    assert payload["base"] == base
    assert payload["head"] == head
    assert isinstance(payload["blocks"], list) and payload["blocks"]
    assert isinstance(payload["diffs"], list)
    assert any(diff.get("probe") == PROBE_ID for diff in payload["diffs"])
    assert payload["survivors"] == []
    assert not (
        root / ".artifacts" / "records" / "aff__evidence-observation"
    ).exists()


def test_r7_fixture_trail_visible_unbound_observations(store: Path) -> None:
    """R7: seeded store subject; aff audit leaves trail-visible unbound observations."""
    base, head = _seed_subject(store, probes=True)
    before_obs = _list_observations(store)
    before_bind = _bound_observation_ids(store)
    proc = _audit(store, base, head)
    payload = _advisory(proc)
    assert payload["base"] == base and payload["head"] == head

    created = _created(before_obs, _list_observations(store))
    audit_rows = _of_technique(created, AUDIT_TECHNIQUE)
    probe_rows = _of_technique(created, PROBES_TECHNIQUE)
    assert audit_rows, created
    assert probe_rows, created
    for row in audit_rows:
        _assert_replay(row, base, head, AUDIT_TECHNIQUE)
    for row in probe_rows:
        _assert_replay(row, base, head, PROBE_ID)

    created_ids = {row["id"] for row in created}
    assert not (created_ids & _bound_observation_ids(store))
    assert not (created_ids & before_bind)

    visible = _trail(store)
    visible_ids = {_observation_id(item) for item in visible}
    assert {row["id"] for row in audit_rows} <= visible_ids
    assert {row["id"] for row in probe_rows} <= visible_ids
    for item in visible:
        if _observation_id(item) not in created_ids:
            continue
        if _technique(item) == AUDIT_TECHNIQUE:
            _assert_replay(item, base, head, AUDIT_TECHNIQUE)
        elif _technique(item) == PROBES_TECHNIQUE:
            _assert_replay(item, base, head, PROBE_ID)
