#!/usr/bin/env python3
import json
from pathlib import Path
# Bundled design in the phase worktree
p = Path("contract/project-design.json")
assert json.loads(p.read_text())["project"] == "orchestra", p
print("ok")
