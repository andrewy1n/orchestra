"""Dashboard phase detail surfaces proof-packet Look/Attention; not Needs-you."""

from __future__ import annotations

import pytest

pytest.importorskip("textual")

from dashboard import model
from dashboard.phase_screen import TAB_LABELS, phase_chips


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
    assert TAB_LABELS["proof"] == "Proof"


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


def test_phase_chip_shows_proof_ready():
    proof = model.ProofView(
        id="rec-x",
        kind="claims",
        revision="abc",
        base="def",
        look="look",
        attention="none",
        machine="m",
        diff="d",
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
        proof=proof,
    )
    colors = {"muted": "dim", "warning": "yellow"}
    assert "proof ready" in phase_chips(detail, colors).plain


def test_soft_and_full_types_include_proof_packet():
    assert "conductor:proof-packet" in model.FULL_TYPES
    assert "conductor:proof-packet" in model.SOFT_TYPES
