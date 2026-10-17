#!/usr/bin/env python3
import json
from pathlib import Path
for p in [Path(".claude-plugin/plugin.json"), Path(".cursor-plugin/plugin.json")]:
    d = json.loads(p.read_text())
    assert d["name"] == "affidavit", p
for p in [Path(".claude-plugin/marketplace.json"), Path(".cursor-plugin/marketplace.json")]:
    m = json.loads(p.read_text())
    names = {m.get("name")} | {x.get("name") for x in m.get("plugins", [])}
    assert "affidavit" in names, (p, names)
print("ok")
