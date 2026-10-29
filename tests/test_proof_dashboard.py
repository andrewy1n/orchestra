"""Dashboard phase detail surfaces proof-packet Look/Attention; not Needs-you."""

from __future__ import annotations

from dashboard.backend import model


def test_proof_not_a_needs_you_kind():
    assert "proof" not in model.NEEDS_ORDER
    assert "proof-packet" not in model.NEEDS_ORDER


def test_tabs_include_proof_when_packet_present():
    proof = model.ProofView(
        id="rec-x",
        kind="claims",
        revision="abc123",
        base="def456",
        look="run pytest",
        attention="none",
        machine="rec-y",
        diff="1 file",
    )
    detail = model.PhaseDetail(
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
    assert "proof" in model.tabs_for(detail)


def test_tabs_omit_proof_when_missing():
    detail = model.PhaseDetail(
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
    assert "proof" not in model.tabs_for(detail)


def test_soft_and_full_types_include_proof_packet():
    assert "conductor:proof-packet" in model.FULL_TYPES
    assert "conductor:proof-packet" in model.SOFT_TYPES
