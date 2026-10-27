"""No tracked file outside the history docs uses a name from before the monorepo."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXEMPT_PREFIXES = (
    ".canon/",
    "docs/history/",
    "docs/plans/monorepo-plan.md",
    "tests/test_names.py",
    "tests/test_orchestra_commands.py",
)
OLD_NAMESPACES = {"score": "plan", "conductor": "run", "tuner": "aff"}
MODULES = {
    "score": REPO_ROOT / "orchestra" / "score" / "schemas" / "score.json",
    "conductor": REPO_ROOT / "orchestra" / "conductor" / "schemas" / "conductor.json",
    "tuner": REPO_ROOT / "orchestra" / "tuner" / "schemas" / "tuner.json",
}


def _old_type_pattern() -> str:
    alternatives = []
    for namespace, path in MODULES.items():
        types = "|".join(sorted(json.loads(path.read_text())["types"], key=len, reverse=True))
        old = OLD_NAMESPACES[namespace]
        alternatives.append(rf"(?<![\w-]){old}(?::|__)(?:{types})(?![\w-])")
    return "|".join(alternatives)


OLD_NAMES = re.compile(
    "|".join(
        [
            r"affidavit",
            r"adaptive[-_]artifacts",
            r"(?<![\w])\.artifacts\b",
            r"\bARTIFACTS_STORE\b",
            r"\bbin/aff\b",
            r"\bbin/aa\b",
            r"\borchestra\.aa\b",
            r"(?<![\w/.-])aff(?: |[\"']\s*,\s*[\"'])(?:verdict|attest|lint|claims?|freeze|audit|trail|bind|unbind|recheck|assertion-red|check|close-batch)\b",
            _old_type_pattern(),
        ]
    ),
    re.IGNORECASE,
)


def _tracked_text_files() -> list[Path]:
    listed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files"], capture_output=True, text=True, check=True
    ).stdout.split()
    files = []
    for rel in listed:
        if rel.startswith(EXEMPT_PREFIXES):
            continue
        path = REPO_ROOT / rel
        if path.is_symlink() or not path.is_file():
            continue
        files.append(path)
    return files


def test_no_tracked_file_uses_an_old_name():
    hits = []
    for path in _tracked_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(text.splitlines(), 1):
            match = OLD_NAMES.search(line)
            if match:
                hits.append(f"{path.relative_to(REPO_ROOT)}:{number}: {match.group(0)}")
    assert hits == []
