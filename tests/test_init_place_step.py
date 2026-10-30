from __future__ import annotations

import re

from conftest import REPO_ROOT

CREATE_EFFORT = "canon create --type score:effort"
ROUTING_BLOCK = re.compile(r"Show the routing line.*?```\n(.*?)```", re.S)


def test_init_skill_runs_orchestra_place_after_creating_effort():
    text = (REPO_ROOT / "skills" / "init" / "SKILL.md").read_text()
    created = text.find(CREATE_EFFORT)
    assert created >= 0, "init skill has no step that creates the effort"
    after = text[created:]
    placed = after.find("orchestra place")
    assert placed >= 0, "init skill does not run orchestra place after creating the effort"
    window = after[max(0, placed - 300) : placed + 300]
    assert re.search(r"routing line[\s\S]{0,300}area", window), window


def test_engage_routing_line_carries_area():
    text = (REPO_ROOT / "skills" / "engage" / "SKILL.md").read_text()
    block = ROUTING_BLOCK.search(text)
    assert block, "engage skill has no routing line block"
    assert re.search(r"^\s*area: ", block.group(1), re.M), block.group(1)
