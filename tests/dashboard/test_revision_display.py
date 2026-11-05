from __future__ import annotations

from pathlib import Path

import pytest

from dashboard.backend import approval
from dashboard.backend.approval import evidence_panels
from dashboard.backend.snapshot import NeedsYouItem
from orchestra.canon.project import open_store


def test_canon_revision_is_not_labeled_as_a_git_revision(
    store: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(approval, "_git_head", lambda root: "abcdef0123456789")
    target = open_store(store, store=store / ".canon")
    target.create(
        record_type="score:effort",
        subject="revision-evidence",
        payload={"goal": "Compare evidence revisions", "kind": "repair"},
    )
    target.create(
        record_type="score:phase",
        subject="revision-evidence",
        payload={"title": "Compare revisions", "ordinal": 1, "effort": "revision-evidence"},
        body="## Problem\n\nCompare revisions.\n\n## Approach\n\nUse one rule.\n\n## Exit criteria\n\nLabels match.",
    )
    acceptance = target.create(
        record_type="score:acceptance",
        subject="revision-evidence",
        payload={
            "criterion": "The evidence label excludes Canon revisions",
            "method": "check",
            "phase": "revision-evidence",
            "effort": "revision-evidence",
            "verify_command": "true",
        },
    )
    check = target.create(
        record_type="tuner:check-run",
        subject="revision-evidence",
        payload={
            "criterion_id": acceptance["id"],
            "revision": "sha256:abcdef0123456789",
            "result": "pass",
            "effort": "revision-evidence",
            "method": "check",
            "signed_by": "",
        },
    )
    item = NeedsYouItem(
        kind="unsigned-check",
        id=check["id"],
        subject=check["subject"],
        text="Compare evidence revisions",
        record_type="tuner:check-run",
    )

    panels = evidence_panels(target, item, root=store, view=None)

    assert len(panels) == 1
    text = panels[0][1]
    assert "sha256:abcdef0123456789" in text
    assert "matches HEAD" not in text
    assert "differs from HEAD" not in text


def test_missing_head_keeps_unknown_revision_label(
    store: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(approval, "_git_head", lambda root: "")
    target = open_store(store, store=store / ".canon")
    target.create(
        record_type="score:effort",
        subject="revision-evidence",
        payload={"goal": "Compare evidence revisions", "kind": "repair"},
    )
    target.create(
        record_type="score:phase",
        subject="revision-evidence",
        payload={"title": "Compare revisions", "ordinal": 1, "effort": "revision-evidence"},
        body="## Problem\n\nCompare revisions.\n\n## Approach\n\nUse one rule.\n\n## Exit criteria\n\nLabels match.",
    )
    acceptance = target.create(
        record_type="score:acceptance",
        subject="revision-evidence",
        payload={
            "criterion": "The evidence label preserves unknown HEAD",
            "method": "check",
            "phase": "revision-evidence",
            "effort": "revision-evidence",
            "verify_command": "true",
        },
    )
    check = target.create(
        record_type="tuner:check-run",
        subject="revision-evidence",
        payload={
            "criterion_id": acceptance["id"],
            "revision": "abcdef0123456789",
            "result": "pass",
            "effort": "revision-evidence",
            "method": "check",
            "signed_by": "",
        },
    )
    item = NeedsYouItem(
        kind="unsigned-check",
        id=check["id"],
        subject=check["subject"],
        text="Compare evidence revisions",
        record_type="tuner:check-run",
    )

    panels = evidence_panels(target, item, root=store, view=None)

    assert len(panels) == 1
    assert "HEAD `unknown`" in panels[0][1]
    assert "matches HEAD" not in panels[0][1]
    assert "differs from HEAD" not in panels[0][1]
