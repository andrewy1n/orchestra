#!/usr/bin/env python3
import json
from pathlib import Path
# Bundled design in the phase worktree
p = Path("contract/project-design.json")
assert json.loads(p.read_text())["project"] == "affidavit", p
# Live store design lives on the primary checkout
primary = Path("/home/andrewyin/se-workflow/.artifacts/project-design.json")
assert json.loads(primary.read_text())["project"] == "affidavit", primary
print("ok")
