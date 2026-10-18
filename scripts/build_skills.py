#!/usr/bin/env python3
"""Generate portable skill references from one shared source.

``shared/`` is the only source. Every advertised skill (a directory under
``skills/`` with a ``SKILL.md``) receives byte-identical copies of the shared
documents in ``references/`` so the skill directory can be installed on its
own. The repository root also keeps generated copies at ``skills/<doc>`` for
repo-local links such as the README.

Usage:
    python3 scripts/build_skills.py
    python3 scripts/build_skills.py --check
    python3 scripts/build_skills.py --check --root <repo-root>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SHARED_DOCS = ("ensure-store.md", "kinds-and-focus.md")
SKILLS_DIRNAME = "skills"
SHARED_DIRNAME = "shared"
REFERENCES_DIRNAME = "references"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def skill_dirs(root: Path) -> list[Path]:
    """Directories under ``skills/`` that advertise a ``SKILL.md``."""
    return sorted(path.parent for path in (root / SKILLS_DIRNAME).glob("*/SKILL.md"))


def generated_pairs(root: Path) -> list[tuple[Path, Path]]:
    """Return ``(source, destination)`` pairs for every generated copy."""
    pairs: list[tuple[Path, Path]] = []
    shared = root / SHARED_DIRNAME
    for doc in SHARED_DOCS:
        source = shared / doc
        for skill in skill_dirs(root):
            pairs.append((source, skill / REFERENCES_DIRNAME / doc))
        # Repo-local compatibility copies; still generated from shared/.
        pairs.append((source, root / SKILLS_DIRNAME / doc))
    return pairs


def build(root: Path) -> list[str]:
    """Write every generated copy. Return error messages."""
    errors: list[str] = []
    for source, destination in generated_pairs(root):
        if not source.is_file():
            errors.append(f"missing source: {source}")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
    return errors


def check(root: Path) -> list[str]:
    """Compare every generated copy with its source. Return drift messages."""
    errors: list[str] = []
    for source, destination in generated_pairs(root):
        if not source.is_file():
            errors.append(f"missing source: {source}")
            continue
        if not destination.is_file():
            errors.append(f"missing generated copy: {destination}")
            continue
        if source.read_bytes() != destination.read_bytes():
            errors.append(f"drift: {destination} differs from {source}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare generated copies with shared/ and exit non-zero on drift",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="repo root to build (default: this checkout)",
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else repo_root()

    if not skill_dirs(root):
        print(f"build_skills: no skills found under {root / SKILLS_DIRNAME}", file=sys.stderr)
        return 2

    if args.check:
        errors = check(root)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            print(
                f"build_skills: {len(errors)} generated file(s) out of date; "
                "run python3 scripts/build_skills.py",
                file=sys.stderr,
            )
            return 1
        print("build_skills: generated references match shared/")
        return 0

    errors = build(root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2
    print(f"build_skills: wrote {len(generated_pairs(root))} generated file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
