from __future__ import annotations

import os
import sys
import tarfile
import tempfile
from pathlib import Path

from orchestra.tools import run_subprocess
from orchestra.tools.git import Git

REPO = Path(__file__).resolve().parent.parent
LAYOUT_TEST = "test_component_layout.py"
COLLECT = [
    "--collect-only",
    "-q",
    "-p",
    "no:cacheprovider",
    "tests",
    "--ignore=tests/canon",
    "--ignore=tests/tuner",
]


def collect(root: Path) -> set[str]:
    result = run_subprocess(
        [sys.executable, "-m", "pytest", *COLLECT],
        cwd=root,
        input=None,
        timeout=None,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(root)},
    )
    if result.returncode != 0:
        sys.exit(f"collection failed in {root}:\n{result.stdout[-2000:]}{result.stderr[-2000:]}")
    ids: set[str] = set()
    for line in result.stdout.splitlines():
        path, separator, rest = line.partition("::")
        if separator:
            ids.add(f"{Path(path).name}::{rest}")
    return ids


def base_ref(git: Git) -> str:
    for ref in ("origin/main", "main"):
        if git.run("rev-parse", "--verify", "--quiet", ref).returncode == 0:
            return ref
    sys.exit("neither origin/main nor main exists")


def main() -> int:
    git = Git(REPO)
    base = git.run("merge-base", "HEAD", base_ref(git)).stdout.strip()
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "base.tar"
        git.run("archive", "--format=tar", f"--output={archive}", base)
        tree = Path(tmp) / "tree"
        with tarfile.open(archive) as bundle:
            bundle.extractall(tree, filter="data")
        before = collect(tree)
    after = collect(REPO)
    added = {i for i in after - before if i.startswith(f"{LAYOUT_TEST}::")}
    missing = before - after
    unexpected = after - before - added
    if missing or unexpected:
        print(f"missing after move: {sorted(missing)[:20]}")
        print(f"unexpected after move: {sorted(unexpected)[:20]}")
        return 1
    print(f"collected {len(before)} before; {len(after)} after (+{len(added)} layout tests)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
