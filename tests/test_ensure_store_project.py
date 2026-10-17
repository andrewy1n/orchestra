"""Bundled contract project id and ensure-store field rewrite."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONTRACT = REPO / "contract" / "project-design.json"

AFFIDAVIT_DESIGN = '{\n  "format": "adaptive-artifacts/project-design@0.3.0",\n  "project": "affidavit"\n}\n'
OTHER_DESIGN = '{\n  "format": "adaptive-artifacts/project-design@0.3.0",\n  "project": "other"\n}\n'


def test_bundled_contract_project_is_orchestra():
    design = json.loads(CONTRACT.read_text())
    assert design["project"] == "orchestra"


def test_affidavit_project_is_rewritten_to_orchestra(tmp_path: Path):
    from orchestra.project_field import rewrite_project_field

    design = tmp_path / "project-affidavit.json"
    design.write_text(AFFIDAVIT_DESIGN)
    outcome = rewrite_project_field(design)
    assert outcome == "rewritten"
    assert json.loads(design.read_text())["project"] == "orchestra"


def test_other_project_is_left_byte_identical(tmp_path: Path):
    from orchestra.project_field import rewrite_project_field

    design = tmp_path / "project-other.json"
    raw = OTHER_DESIGN.encode()
    design.write_bytes(raw)
    outcome = rewrite_project_field(design)
    assert outcome == "stopped"
    assert design.read_bytes() == raw


def test_orchestra_project_is_already_current(tmp_path: Path):
    from orchestra.project_field import rewrite_project_field

    design = tmp_path / "project-orchestra.json"
    raw = AFFIDAVIT_DESIGN.replace('"affidavit"', '"orchestra"').encode()
    design.write_bytes(raw)
    outcome = rewrite_project_field(design)
    assert outcome == "current"
    assert design.read_bytes() == raw
