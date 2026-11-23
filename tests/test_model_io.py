from __future__ import annotations

from pathlib import Path

from tests.model_io_support import PACKAGE, io_violations, undeclared_packages

MODEL = "model"
OPERATION = "operation"

DECLARATIONS = {
    "score": MODEL,
    "score/cli.py": OPERATION,
    "score/facts": MODEL,
    "score/planning": MODEL,
    "score/schemas": MODEL,
    "score/workflow": MODEL,
    "composer": MODEL,
    "composer/cli.py": OPERATION,
    "composer/schemas": MODEL,
    "tuner": MODEL,
    "tuner/cli.py": OPERATION,
    "tuner/verify_plugins.py": OPERATION,
    "tuner/authoring": OPERATION,
    "tuner/evidence": OPERATION,
    "tuner/evidence/signing": OPERATION,
    "tuner/plugins": OPERATION,
    "tuner/schemas": MODEL,
    "conductor": MODEL,
    "conductor/briefs": OPERATION,
    "conductor/briefs/sections": MODEL,
    "conductor/cli": OPERATION,
    "conductor/landing": OPERATION,
    "conductor/phases": MODEL,
    "conductor/phases/progress": OPERATION,
    "conductor/phases/workflow": MODEL,
    "conductor/schemas": MODEL,
    "conductor/tasks": OPERATION,
    "conductor/tasks/close": OPERATION,
    "conductor/tasks/redispatch": MODEL,
    "conductor/verification": OPERATION,
    "conductor/verification/evidence": OPERATION,
    "conductor/verification/review": MODEL,
    "conductor/verification/suite": OPERATION,
}


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_every_package_is_declared_model_or_operation():
    assert undeclared_packages(PACKAGE, DECLARATIONS) == []


def test_declarations_name_only_model_or_operation():
    assert set(DECLARATIONS.values()) <= {MODEL, OPERATION}


def test_model_packages_do_no_io():
    assert io_violations(PACKAGE, DECLARATIONS) == []


def test_undeclared_package_is_reported(tmp_path: Path):
    _write(tmp_path, "score/new/__init__.py", "")
    assert undeclared_packages(tmp_path, {"score": MODEL}) == ["score/new"]


def test_model_package_io_is_reported(tmp_path: Path):
    _write(
        tmp_path,
        "score/leak.py",
        "import subprocess\n"
        "import os\n"
        "from pathlib import Path\n"
        "def f(p: Path):\n"
        "    open('x')\n"
        "    os.listdir('.')\n"
        "    return p.read_text()\n",
    )
    found = io_violations(tmp_path, {"score": MODEL})
    assert [v.split(": ", 1)[0] for v in found] == [
        "score/leak.py:1",
        "score/leak.py:5",
        "score/leak.py:6",
        "score/leak.py:7",
    ]


def test_operation_package_may_do_io(tmp_path: Path):
    _write(tmp_path, "conductor/landing/run.py", "import subprocess\nopen('x')\n")
    assert io_violations(tmp_path, {"conductor/landing": OPERATION}) == []


def test_pure_model_module_passes(tmp_path: Path):
    _write(tmp_path, "score/pure.py", "import json\nimport os\nx = os.path.join('a', 'b')\n")
    assert io_violations(tmp_path, {"score": MODEL}) == []


def test_module_declaration_overrides_package(tmp_path: Path):
    _write(tmp_path, "score/cli.py", "open('x')\n")
    _write(tmp_path, "score/other.py", "open('x')\n")
    found = io_violations(tmp_path, {"score": MODEL, "score/cli.py": OPERATION})
    assert found == ["score/other.py:1: calls open()"]
