"""Dashboard phase detail surfaces proof-packet Look/Attention; not Needs-you."""

from __future__ import annotations

from dashboard.backend import phase as phase_mod
from dashboard.backend import records
from dashboard.backend import snapshot as snapshot_mod


def test_proof_not_a_needs_you_kind():
    assert "proof" not in snapshot_mod.NEEDS_ORDER
    assert "proof-packet" not in snapshot_mod.NEEDS_ORDER


def test_tabs_include_proof_when_packet_present():
    proof = phase_mod.ProofView(
        id="rec-x",
        kind="claims",
        revision="abc123",
        base="def456",
        look="run pytest",
        attention="none",
        machine="rec-y",
        diff="1 file",
    )
    detail = phase_mod.PhaseDetail(
        subject="ph",
        effort="eff",
        title="T",
        state="done",
        awaiting_signoff=False,
        body="",
        decisions=[],
        constraints=[],
        tasks=[],
        structured=True,
        proof=proof,
    )
    assert "proof" in phase_mod.tabs_for(detail)


def test_tabs_omit_proof_when_missing():
    detail = phase_mod.PhaseDetail(
        subject="ph",
        effort="eff",
        title="T",
        state="done",
        awaiting_signoff=False,
        body="",
        decisions=[],
        constraints=[],
        tasks=[],
        structured=True,
        proof=None,
    )
    assert "proof" not in phase_mod.tabs_for(detail)


def test_soft_and_full_types_include_proof_packet():
    assert "conductor:proof-packet" in snapshot_mod.FULL_TYPES
    assert "conductor:proof-packet" in records.SOFT_TYPES
