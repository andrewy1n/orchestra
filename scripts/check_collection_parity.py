import os
import subprocess
import sys
import tempfile
from pathlib import Path

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


def git(*args: str, cwd: Path = REPO) -> bytes:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True).stdout


def collect(root: Path) -> set[str]:
    env = {**os.environ, "PYTHONPATH": str(root)}
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *COLLECT],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.exit(f"collection failed in {root}:\n{result.stdout[-2000:]}{result.stderr[-2000:]}")
    ids = set()
    for line in result.stdout.splitlines():
        if "::" not in line:
            continue
        path, _, rest = line.partition("::")
        ids.add(f"{Path(path).name}::{rest}")
    return ids


def main() -> int:
    base = git("merge-base", "HEAD", "main").decode().strip()
    with tempfile.TemporaryDirectory() as tmp:
        archive = subprocess.Popen(["git", "archive", base], cwd=REPO, stdout=subprocess.PIPE)
        subprocess.run(["tar", "-x", "-C", tmp], stdin=archive.stdout, check=True)
        archive.wait()
        before = collect(Path(tmp))
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
