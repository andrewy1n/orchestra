"""Integration: create proof-packet via CLI shape and parse Look for dashboard."""

from __future__ import annotations


import helpers as h
from dashboard import model


def test_smoke_proof_packet_look_usable_from_contract_and_body_shape():
    assert h.record_def("proof-packet")["id"] == "conductor:proof-packet"

    look = "open dashboard phase detail Proof for phase-proof-packet"
    sample = (
        f"## Look\n\n{look}\n\n"
        "## Machine\n\ncheck-run: none\n\n"
        "## Attention\n\nnone\n\n"
        "## Diff\n\nno tree change\n"
    )
    assert model._section(sample, "Look").strip() == look
    assert model._section(sample, "Attention").strip() == "none"
    proof = model.ProofView(
        id="rec-smoke",
        kind="claims",
        revision="04737710" * 5,
        base="main",
        look=model._section(sample, "Look"),
        attention=model._section(sample, "Attention"),
        machine=model._section(sample, "Machine"),
        diff=model._section(sample, "Diff"),
    )
    detail = model.PhaseDetail(
        subject="phase-proof-packet",
        effort="workflow-loop",
        title="Phase-end proof packet",
        state="done",
        awaiting_signoff=False,
        body="",
        decisions=[],
        constraints=[],
        tasks=[],
        proof=proof,
    )
    assert "proof" in model.tabs_for(detail)
    assert "dashboard phase detail Proof" in detail.proof.look
