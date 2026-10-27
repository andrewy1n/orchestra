"""Schema defines conductor:proof-packet."""

from __future__ import annotations

import helpers as h


def test_proof_packet_type_and_sections():
    proof = h.record_def("proof-packet")
    assert proof["id"] == "conductor:proof-packet"
    assert proof["lifecycle"]["name"] == "event"
    assert proof["payload"] == ["phase", "effort", "revision", "base", "kind"]
    assert proof["payload_enum"]["kind"] == [
        "demo",
        "commands",
        "claims",
        "audit-triage",
        "mixed",
    ]
    assert proof["required_sections"] == ["Look", "Machine", "Attention", "Diff"]
