"""Contract defines project:proof-packet and handoff latest-proof."""

from __future__ import annotations

import json

from conftest import REPO_ROOT

CONTRACT = REPO_ROOT / "contract" / "project-design.json"


def _design() -> dict:
    return json.loads(CONTRACT.read_text())


def test_proof_packet_type_and_sections():
    records = {r["name"]: r for r in _design()["records"]}
    proof = records["proof-packet"]
    assert proof["pattern"] == "observation"
    assert proof["payload"] == ["phase", "effort", "revision", "base", "kind"]
    assert proof["payload_enum"]["kind"] == [
        "demo",
        "commands",
        "claims",
        "audit-triage",
        "mixed",
    ]
    assert proof["required_sections"] == ["Look", "Machine", "Attention", "Diff"]


def test_handoff_latest_proof_role():
    handoff = next(v for v in _design()["views"] if v["name"] == "handoff")
    roles = {r["name"]: r for r in handoff["roles"]}
    role = roles["latest-proof"]
    assert role["occupant"] == "proof-packet"
    assert "revision" in role["requires_payload"]
    assert "kind" in role["requires_payload"]
