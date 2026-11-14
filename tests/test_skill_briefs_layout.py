import re
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT

SKILLS_DIR = REPO_ROOT / "skills"
SKILL_FILES = sorted(SKILLS_DIR.glob("*/SKILL.md"))
NON_STEP_SKILLS = {"init", "engage", "triage-ideas", "analyze-sessions"}
NO_DO_NOT_SECTION = {"analyze-sessions"}
DELETED_ROOT_COPIES = (
    "ensure-store.md",
    "intent-qa.md",
    "kinds-and-focus.md",
    "verification-policy.md",
)


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "missing frontmatter"
    fields: dict[str, str] = {}
    key = ""
    for line in match.group(1).splitlines():
        if re.match(r"^\w[\w-]*:", line):
            key, _, value = line.partition(":")
            fields[key] = value.strip()
        elif key:
            fields[key] = f"{fields[key]} {line.strip()}".strip()
    return fields


def _ids(paths: list[Path]) -> list[str]:
    return [p.parent.name for p in paths]


def test_skill_files_found() -> None:
    assert len(SKILL_FILES) >= 11


@pytest.mark.parametrize("path", SKILL_FILES, ids=_ids(SKILL_FILES))
def test_skill_brief_line_frontmatter(path: Path) -> None:
    fields = _frontmatter(path.read_text())
    assert fields.get("name") == path.parent.name
    assert fields.get("description", "").strip() not in ("", ">-", ">", "|")


@pytest.mark.parametrize("path", SKILL_FILES, ids=_ids(SKILL_FILES))
def test_skill_brief_line_instruction(path: Path) -> None:
    name = path.parent.name
    text = _flat(path.read_text())
    if name in NON_STEP_SKILLS:
        assert f"orchestra workflow brief --skill {name}" in text
    else:
        assert f"orchestra workflow brief <phase> {name}" in text or (
            "orchestra workflow brief <phase> <step>" in text
        )
        assert "orchestra workflow next" in text


@pytest.mark.parametrize("path", SKILL_FILES, ids=_ids(SKILL_FILES))
def test_skill_brief_line_install_stop(path: Path) -> None:
    text = _flat(path.read_text())
    assert "stop and tell the user to install orchestra" in text


@pytest.mark.parametrize("path", SKILL_FILES, ids=_ids(SKILL_FILES))
def test_skill_brief_line_do_not_section(path: Path) -> None:
    if path.parent.name in NO_DO_NOT_SECTION:
        pytest.skip("skill has no Do not section")
    assert re.search(r"^## Do not\s*$", path.read_text(), re.MULTILINE)


@pytest.mark.parametrize("path", SKILL_FILES, ids=_ids(SKILL_FILES))
def test_skill_no_references_links(path: Path) -> None:
    assert "references/" not in path.read_text()


def test_deleted_paths_shared_dir_absent() -> None:
    assert not (REPO_ROOT / "shared").exists()


def test_deleted_paths_build_script_absent() -> None:
    assert not (REPO_ROOT / "scripts" / "build_skills.py").exists()


def test_deleted_paths_skill_references_dirs_absent() -> None:
    leftovers = sorted(str(p.relative_to(REPO_ROOT)) for p in SKILLS_DIR.glob("*/references"))
    assert leftovers == []


@pytest.mark.parametrize("filename", DELETED_ROOT_COPIES)
def test_deleted_paths_root_skill_copy_absent(filename: str) -> None:
    assert not (SKILLS_DIR / filename).exists()
