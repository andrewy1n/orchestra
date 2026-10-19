#!/usr/bin/env python3
"""Generate every derived copy from its one authored source.

Two families of generated file:

* ``shared/`` documents, copied byte-for-byte into every skill's
  ``references/`` so the skill directory installs on its own. The repository
  root also keeps generated copies at ``skills/<doc>`` for repo-local links
  such as the README.
* ``agents/reviewer.prompt.md`` — the one authored reviewer prompt. Its bytes
  become ``skills/execute-phase/references/se-reviewer.md`` (the prompt a
  skill hands a host subagent when the install provides no reviewer agent),
  and it is rendered into ``agents/se-reviewer.md`` with the frontmatter
  Claude Code reads. The rendering uses ``installer.agents`` so the checkout
  copy and every installed agent share one renderer.

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

REVIEWER_PROMPT = Path("agents") / "reviewer.prompt.md"
REVIEWER_AGENT = Path("agents") / "se-reviewer.md"
REVIEWER_SKILL = "execute-phase"
REVIEWER_REFERENCE = Path(REFERENCES_DIRNAME) / "se-reviewer.md"

_CHECKOUT_ROOT = Path(__file__).resolve().parent.parent
if str(_CHECKOUT_ROOT) not in sys.path:
    sys.path.insert(0, str(_CHECKOUT_ROOT))

# One renderer for the checkout copy and every host install.
from installer.agents import load as load_agent  # noqa: E402
from installer.agents import render as render_agent  # noqa: E402


def repo_root() -> Path:
    return _CHECKOUT_ROOT


def skill_dirs(root: Path) -> list[Path]:
    """Directories under ``skills/`` that advertise a ``SKILL.md``."""
    return sorted(path.parent for path in (root / SKILLS_DIRNAME).glob("*/SKILL.md"))


def generated_pairs(root: Path) -> list[tuple[Path, Path]]:
    """Return ``(source, destination)`` pairs copied byte-for-byte."""
    pairs: list[tuple[Path, Path]] = []
    shared = root / SHARED_DIRNAME
    for doc in SHARED_DOCS:
        source = shared / doc
        for skill in skill_dirs(root):
            pairs.append((source, skill / REFERENCES_DIRNAME / doc))
        # Repo-local compatibility copies; still generated from shared/.
        pairs.append((source, root / SKILLS_DIRNAME / doc))
    # The reviewer prompt is handed to a host subagent that has no installed
    # reviewer agent; the skill directory must carry it verbatim.
    reviewer_skill = root / SKILLS_DIRNAME / REVIEWER_SKILL
    if reviewer_skill.is_dir():
        pairs.append((root / REVIEWER_PROMPT, reviewer_skill / REVIEWER_REFERENCE))
    return pairs


def rendered_agent(root: Path) -> tuple[Path, str | None]:
    """The checkout's reviewer agent, rendered like a Claude install.

    ``None`` means the canonical prompt is absent; the caller reports it.
    """
    if not (root / REVIEWER_PROMPT).is_file():
        return root / REVIEWER_AGENT, None
    return root / REVIEWER_AGENT, render_agent("claude", load_agent(root))


def build(root: Path) -> list[str]:
    """Write every generated copy. Return error messages."""
    errors: list[str] = []
    for source, destination in generated_pairs(root):
        if not source.is_file():
            errors.append(f"missing source: {source}")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
    destination, text = rendered_agent(root)
    if text is None:
        errors.append(f"missing source: {root / REVIEWER_PROMPT}")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
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
    destination, text = rendered_agent(root)
    if text is None:
        errors.append(f"missing source: {root / REVIEWER_PROMPT}")
    elif not destination.is_file():
        errors.append(f"missing generated copy: {destination}")
    elif destination.read_text(encoding="utf-8") != text:
        errors.append(f"drift: {destination} differs from {root / REVIEWER_PROMPT}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare generated copies with their sources and exit non-zero on drift",
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
        print("build_skills: generated files match their sources")
        return 0

    errors = build(root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2
    print(f"build_skills: wrote {len(generated_pairs(root)) + 1} generated file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
