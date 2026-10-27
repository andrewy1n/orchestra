"""Evidence-layout allows the library import and project record types (R6)."""

from __future__ import annotations

from pathlib import Path

import test_evidence_layout as layout

_SOURCE = '''\
"""Store client."""

from canon.project import Project

OBSERVATION = "aff:evidence-observation"
BINDING = "aff:evidence-binding"


def label(project: Project) -> str:
    return OBSERVATION if project is not None else BINDING
'''


def test_store_client_layout_allows_library_and_record_types(
    tmp_path: Path, monkeypatch
) -> None:
    """R6: the evidence-layout test passes when affidavit imports canon and names aff: record types."""
    package = tmp_path / "affidavit"
    package.mkdir()
    (package / "library_client.py").write_text(_SOURCE, encoding="utf-8")
    monkeypatch.setattr(layout, "REPO_ROOT", tmp_path)
    rejected = False
    try:
        layout.test_no_store_tokens()
    except AssertionError:
        rejected = True
    assert not rejected, (
        "tests/test_store_client_layout.py::test_store_client_layout_allows_library_and_record_types "
        "must pass when affidavit source imports canon and names aff: record types"
    )
