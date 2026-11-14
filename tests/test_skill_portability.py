"""Every advertised skill installs as one self-contained SKILL.md directory.

R1: a skill directory contains every file its instructions reference, and no
reference leaves the directory. A bare ``agents/...`` path is an authored
source outside the skill.
R4: every ``SKILL.md`` has frontmatter whose ``name`` equals its directory and
whose ``description`` is non-empty.
R6: no skill body names a checkout path or a ``<plugin>`` root for a runtime
call; skills call ``orchestra`` and ``canon`` by name. A checkout path to
the removed ``aff`` binary is still rejected.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
SECTIONS = ROOT / "orchestra" / "conductor" / "briefs" / "sections"

_FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")
_INLINE_PATH = re.compile(r"`((?:\.\.?/|references/)[^`\s]+)`")
#: Authored sources outside the skill directory.
#: A skill that names one directly would break once it is installed alone.
_OUTSIDE_SKILL_DIRS = ("agents",)
_BARE_OUTSIDE_PATH = re.compile(r"`((?:" + "|".join(_OUTSIDE_SKILL_DIRS) + r")/[^`\s]+)`")

_CHECKOUT_PATH = re.compile(
    r"(?:^|[\s`(])(?:\.{1,2}/|~/|/)[^\s`)]*/(?:bin/)?(?:orchestra|aff|canon)(?=\s|$|[;&|])"
)
_CHECKOUT_RELATIVE = re.compile(r"(?:^|[\s`(])bin/orchestra\b")
_PLUGIN_ROOT = re.compile(r"<plugin>")
#: Importable module APIs (`orchestra.conductor.reviewer`, `orchestra.conductor.suite.poll_suite`,
#: `orchestra.store`) are not a runtime surface an installed CLI exposes.
_MODULE_API = re.compile(r"`?\borchestra\.(?!toml\b)([a-z_][A-Za-z0-9_]*)")


def advertised_skills(root: Path = ROOT) -> list[Path]:
    return sorted(path.parent for path in (root / "skills").glob("*/SKILL.md"))


def parse_frontmatter(text: str) -> dict[str, str] | None:
    match = _FRONTMATTER.match(text)
    if not match:
        return None
    meta: dict[str, str] = {}
    key: str | None = None
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if line[:1].isspace():
            if key:
                meta[key] = f"{meta.get(key, '')} {line.strip()}".strip()
            continue
        name, sep, value = line.partition(":")
        if not sep:
            continue
        key = name.strip()
        assert key
        meta[key] = value.strip()
    return meta


def description_of(meta: dict[str, str]) -> str:
    value = meta.get("description", "").strip()
    if value[:1] in {">", "|"}:
        value = value[1:].lstrip("-").strip()
    return value


def referenced_paths(text: str) -> list[str]:
    """Relative paths a skill instruction points at."""
    targets: list[str] = []
    for match in _LINK.finditer(text):
        target = match.group(1).strip().strip("<>")
        if target.startswith(("http://", "https://", "mailto:", "#", "data:")):
            continue
        targets.append(target.split("#", 1)[0])
    for pattern in (_INLINE_PATH, _BARE_OUTSIDE_PATH):
        for match in pattern.finditer(text):
            targets.append(match.group(1).split("#", 1)[0])
    return [target for target in targets if target]


def path_errors(skill_dir: Path, text: str) -> list[str]:
    errors: list[str] = []
    for target in referenced_paths(text):
        parts = Path(target).parts
        leaves = (
            target.startswith(("/", "~"))
            or ".." in parts
            or (parts and parts[0] in _OUTSIDE_SKILL_DIRS)
        )
        if leaves:
            errors.append(f"{skill_dir.name}: referenced path leaves the skill directory: {target}")
            continue
        if not (skill_dir / target).exists():
            errors.append(f"{skill_dir.name}: referenced path is missing: {target}")
    return errors


def runtime_call_errors(text: str) -> list[str]:
    errors: list[str] = []
    if _PLUGIN_ROOT.search(text):
        errors.append("names a <plugin> root for a runtime call")
    if _CHECKOUT_PATH.search(text):
        errors.append("names a path-qualified runtime command")
    if _CHECKOUT_RELATIVE.search(text):
        errors.append("names a checkout-relative runtime command")
    return errors


def module_api_errors(text: str) -> list[str]:
    """Module names a skill tells the agent to import instead of a command."""
    errors: list[str] = []
    seen: set[str] = set()
    for match in _MODULE_API.finditer(text):
        module = match.group(1)
        if module in seen:
            continue
        seen.add(module)
        errors.append(f"names the module API orchestra.{module} instead of a CLI command")
    return errors


@pytest.mark.parametrize("skill_dir", advertised_skills(), ids=lambda path: path.name)
def test_paths_every_reference_stays_inside_the_skill_directory(skill_dir: Path):
    errors: list[str] = []
    for markdown in sorted(skill_dir.rglob("*.md")):
        errors.extend(path_errors(skill_dir, markdown.read_text()))
    assert not errors, "\n".join(errors)


def test_paths_planted_parent_reference_is_rejected(tmp_path: Path):
    skill = tmp_path / "skills" / "bad" / "references"
    skill.mkdir(parents=True)
    text = (
        "---\nname: bad\ndescription: bad skill\n---\n\nSee [store](../outside/ensure-store.md).\n"
    )
    errors = path_errors(skill.parent, text)
    assert any("leaves the skill directory" in error for error in errors), errors


def test_paths_planted_missing_reference_is_rejected(tmp_path: Path):
    skill = tmp_path / "skills" / "bad"
    skill.mkdir(parents=True)
    text = "---\nname: bad\ndescription: bad skill\n---\n\nRead `references/missing.md`.\n"
    errors = path_errors(skill, text)
    assert any("missing" in error for error in errors), errors


def test_paths_planted_bare_agents_reference_is_rejected(tmp_path: Path):
    skill = tmp_path / "skills" / "bad"
    skill.mkdir(parents=True)
    text = "---\nname: bad\ndescription: bad skill\n---\n\nDispatch `agents/reviewer.md`.\n"
    errors = path_errors(skill, text)
    assert any("leaves the skill directory" in error for error in errors), errors


def test_paths_planted_bare_agents_link_is_rejected(tmp_path: Path):
    skill = tmp_path / "skills" / "bad"
    skill.mkdir(parents=True)
    text = "---\nname: bad\ndescription: bad skill\n---\n\nFollow [reviewer](agents/reviewer.md).\n"
    errors = path_errors(skill, text)
    assert any("leaves the skill directory" in error for error in errors), errors


def test_paths_examples_naming_other_roots_are_not_skill_references(tmp_path: Path):
    """Prose may name e.g. ``contract/project-design.json`` as a fix target."""
    skill = tmp_path / "skills" / "bad"
    skill.mkdir(parents=True)
    text = (
        "---\nname: bad\ndescription: bad skill\n---\n\n"
        "Fix goes in `contract/project-design.json`.\n"
    )
    assert path_errors(skill, text) == []


def test_paths_runtime_calls_use_named_commands_only():
    errors: list[str] = []
    for skill_dir in advertised_skills():
        for markdown in sorted(skill_dir.rglob("*.md")):
            for error in runtime_call_errors(markdown.read_text()):
                errors.append(f"{markdown.relative_to(SKILLS)}: {error}")
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize(
    "text",
    [
        "Run `<plugin>/bin/orchestra check`.\n",
        "Run `bin/orchestra close-batch`.\n",
        "Run `/usr/local/bin/canon validate`.\n",
    ],
)
def test_paths_planted_runtime_checkout_paths_are_rejected(text: str):
    assert runtime_call_errors(text), text


def test_paths_named_runtime_commands_are_allowed():
    text = (
        "Run `orchestra check`, `orchestra close-batch`, "
        "`canon validate`, and `orchestra verify verdict`.\n"
    )
    assert runtime_call_errors(text) == []


def test_runtime_references_name_cli_commands_not_module_apis():
    errors: list[str] = []
    paths = [*sorted(SKILLS.rglob("*.md")), *sorted(SECTIONS.glob("*.md"))]
    for path in paths:
        for error in module_api_errors(path.read_text()):
            errors.append(f"{path.relative_to(ROOT)}: {error}")
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize(
    "text",
    [
        "Build the brief with `orchestra.conductor.reviewer.build_reviewer_brief`.\n",
        "Poll with `orchestra.conductor.suite.poll_suite`.\n",
        "Call through `orchestra.store`.\n",
    ],
)
def test_runtime_module_api_references_are_rejected(text: str):
    assert module_api_errors(text), text


def test_runtime_cli_subcommands_are_allowed():
    text = (
        "Run `orchestra review-brief`, `orchestra suite poll`, "
        "`orchestra store path`, and `orchestra store run -- list`.\n"
    )
    assert module_api_errors(text) == []


@pytest.mark.parametrize("skill_dir", advertised_skills(), ids=lambda path: path.name)
def test_frontmatter_name_matches_directory_and_description_is_nonempty(skill_dir: Path):
    meta = parse_frontmatter((skill_dir / "SKILL.md").read_text())
    assert meta is not None, f"{skill_dir.name}/SKILL.md has no frontmatter"
    assert meta.get("name") == skill_dir.name, (
        f"{skill_dir.name}/SKILL.md name is {meta.get('name')!r}"
    )
    assert description_of(meta), f"{skill_dir.name}/SKILL.md needs a description"
