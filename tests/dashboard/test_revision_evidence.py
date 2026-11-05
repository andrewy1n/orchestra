from __future__ import annotations

from pathlib import Path

import pytest
from conftest import git

from dashboard.backend.approval import evidence_panels
from dashboard.backend.snapshot import NeedsYouItem
from orchestra.canon.project import open_store


@pytest.mark.parametrize(
    ("revision_case", "matches_head"),
    [
        pytest.param("exact", True, id="exact"),
        pytest.param("surrounding-whitespace", True, id="surrounding-whitespace"),
        pytest.param("mixed-case", True, id="mixed-case"),
        pytest.param("seven-character-prefix", True, id="seven-character-prefix"),
        pytest.param(
            "normalized-seven-character-prefix",
            True,
            id="normalized-seven-character-prefix",
        ),
        pytest.param("six-character-prefix", False, id="six-character-prefix"),
        pytest.param("unrelated", False, id="unrelated"),
    ],
)
def test_evidence_label_uses_shared_revision_rule(
    store: Path,
    revision_case: str,
    matches_head: bool,
) -> None:
    head_result = git(store, "rev-parse", "HEAD")
    assert head_result.returncode == 0, head_result.stderr
    head = head_result.stdout.strip()
    checked_revision = {
        "exact": head,
        "surrounding-whitespace": f" \t{head}\n",
        "mixed-case": head.upper(),
        "seven-character-prefix": head[:7],
        "normalized-seven-character-prefix": f" \t{head[:7].upper()}\n",
        "six-character-prefix": head[:6],
        "unrelated": ("0" if head[0] != "0" else "1") + head[1:],
    }[revision_case]
    target = open_store(store, store=store / ".canon")
    target.create(
        record_type="score:effort",
        subject="revision-evidence",
        payload={"goal": "Compare evidence revisions", "kind": "repair"},
    )
    target.create(
        record_type="score:phase",
        subject="revision-evidence",
        payload={
            "title": "Compare evidence revisions",
            "ordinal": 1,
            "effort": "revision-evidence",
        },
        body="## Problem\n\nCompare revisions.\n\n## Approach\n\nUse one rule.\n\n## Exit criteria\n\nLabels match the rule.",
    )
    acceptance = target.create(
        record_type="score:acceptance",
        subject="revision-evidence",
        payload={
            "criterion": "The evidence label follows the revision rule",
            "method": "check",
            "phase": "revision-evidence",
            "effort": "revision-evidence",
            "verify_command": "uv run pytest tests/dashboard/test_revision_evidence.py",
        },
    )
    check = target.create(
        record_type="tuner:check-run",
        subject="revision-evidence",
        payload={
            "criterion_id": acceptance["id"],
            "revision": checked_revision,
            "result": "pass",
            "effort": "revision-evidence",
            "method": "manual",
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
    title, text = panels[0]
    assert title == "Evidence"
    assert f"HEAD `{head[:7]}`" in text
    assert (" · matches HEAD" in text) is matches_head
    assert (" · **differs from HEAD**" in text) is not matches_head
