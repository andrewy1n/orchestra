from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from conftest import CANON_CMD, REPO_ROOT, make_git_repo

SCORE_MODULE = REPO_ROOT / "orchestra" / "score" / "schemas" / "score.json"


def _canon(root: Path, schema_path: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CANON_SCHEMA_PATH": str(schema_path)}
    return subprocess.run(
        [*CANON_CMD, "--root", str(root), *args], capture_output=True, text=True, env=env
    )


def _output(result: subprocess.CompletedProcess) -> str:
    return result.stdout + result.stderr


def test_migrated_fixture_store_validates_without_merged_from() -> None:
    legacy = copy.deepcopy(json.loads(SCORE_MODULE.read_text()))
    legacy["version"] = "1.6.0"
    legacy["migrations"] = []
    legacy["types"]["effort"]["fields"]["merged_from"] = {
        "list": {"type": "string"},
        "optional": True,
    }
    schema_dir = Path(tempfile.mkdtemp(prefix="score-legacy-"))
    legacy_path = schema_dir / "score.json"
    legacy_path.write_text(json.dumps(legacy))
    root = make_git_repo()
    try:
        assert _canon(root, legacy_path, "init", "--schemas", "score").returncode == 0
        for subject, merged in (("alpha", ["old-a", "old-b"]), ("beta", [])):
            payload = {"goal": "Ship it", "kind": "deliver", "merged_from": merged}
            created = _canon(
                root,
                legacy_path,
                "create",
                "--type",
                "score:effort",
                "--subject",
                subject,
                "--payload",
                json.dumps(payload),
            )
            assert created.returncode == 0, _output(created)

        sync = _canon(root, SCORE_MODULE, "schemas", "sync")
        assert sync.returncode == 0, _output(sync)
        assert _canon(root, SCORE_MODULE, "validate").returncode == 0

        snapshot = json.loads((root / ".canon" / "schemas" / "score.json").read_text())
        assert "merged_from" not in snapshot["types"]["effort"]["fields"]
        shown = _canon(root, SCORE_MODULE, "list", "--type", "score:effort")
        assert shown.returncode == 0, _output(shown)
        assert "merged_from" not in shown.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(schema_dir, ignore_errors=True)
