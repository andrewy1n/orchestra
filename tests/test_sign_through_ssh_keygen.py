from __future__ import annotations

import ast
from pathlib import Path

SIGN = Path(__file__).resolve().parents[1] / "orchestra" / "tuner" / "sign.py"


def test_sign_module_uses_ssh_keygen_client() -> None:
    tree = ast.parse(SIGN.read_text(encoding="utf-8"))
    imported_modules: set[str] = set()
    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.add((node.module or "").split(".")[0])
            imported_names.update(alias.name for alias in node.names)
    assert "subprocess" not in imported_modules
    assert "SshKeygen" in imported_names
