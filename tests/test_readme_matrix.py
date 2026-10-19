"""README host matrix and install commands match the installer.

The provider matrix in ``installer/providers.json`` is the source of truth.
These tests read it through the installer and compare every row and command
that the README documents, so a new provider or a renamed root cannot leave
the docs stale.
"""

from __future__ import annotations

import re
import subprocess
import sys

from conftest import REPO_ROOT
from installer.matrix import load_matrix

HEADING = "## Install with the CLI"
AGENT_SKILLS_HEADING = "#### Codex / other Agent Skills hosts"
EXPECTED_HEADER = (
    "Host",
    "Provider id",
    "Kind",
    "Project root",
    "Global root",
    "Skills profile",
)
DOCUMENTED_FLAGS = (
    "--only",
    "--all",
    "--dry-run",
    "--global",
    "--copy",
    "--uninstall",
    "--home",
)
DOCUMENTED_COMMANDS = (
    "check",
    "close-batch",
    "install",
    "contract",
    "project-field",
    "sessions",
    "review-brief",
    "suite",
    "store",
)
SEPARATOR = re.compile(r":?-{3,}:?")


def _readme() -> str:
    return (REPO_ROOT / "README.md").read_text(encoding="utf-8")


def _section_of(heading: str) -> str:
    text = _readme()
    marker = f"\n{heading}\n"
    start = text.index(marker) + 1
    rest = text[start + len(heading) :]
    end = rest.find("\n## ")
    return rest if end < 0 else rest[:end]


def _section() -> str:
    return _section_of(HEADING)


def _agent_skills_section() -> str:
    text = _readme()
    start = text.index(AGENT_SKILLS_HEADING)
    rest = text[start + len(AGENT_SKILLS_HEADING) :]
    end = rest.find("\n## ")
    return rest if end < 0 else rest[:end]


def _generated_skills() -> list[str]:
    return sorted(
        child.name
        for child in (REPO_ROOT / "skills").iterdir()
        if (child / "SKILL.md").is_file()
    )


def _plain(cell: str) -> str:
    return cell.strip().strip("`").strip()


def _host_matrix(section: str) -> tuple[list[str], list[list[str]]]:
    header: list[str] | None = None
    rows: list[list[str]] = []
    in_table = False
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table:
                break
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not in_table:
            if cells and cells[0] == "Host":
                header = cells
                in_table = True
            continue
        if all(SEPARATOR.fullmatch(cell) for cell in cells):
            continue
        rows.append(cells)
    assert header is not None, f"no host matrix table under {HEADING!r}"
    return header, rows


def test_cli_install_is_documented():
    section = _section()
    assert (
        'uv tool install "git+https://github.com/andrewy1n/orchestra.git@<ref>"'
        in section
    )
    assert "./bin/orchestra install" in section


def test_host_matrix_matches_provider_matrix():
    header, rows = _host_matrix(_section())
    assert tuple(header) == EXPECTED_HEADER
    column = {name: index for index, name in enumerate(header)}
    providers = load_matrix()

    assert [_plain(row[column["Provider id"]]) for row in rows] == [
        provider.id for provider in providers
    ]

    for provider, row in zip(providers, rows):
        assert _plain(row[column["Host"]]) == provider.name, provider.id
        assert _plain(row[column["Provider id"]]) == provider.id
        assert _plain(row[column["Kind"]]) == provider.kind, provider.id
        assert _plain(row[column["Project root"]]) == provider.project_root, provider.id
        assert _plain(row[column["Global root"]]) == provider.global_root, provider.id
        profile = row[column["Skills profile"]]
        if provider.profile is None:
            assert profile == "—", provider.id
        else:
            assert _plain(profile) == provider.profile, provider.id


def test_every_provider_has_a_documented_install_command():
    section = _section()
    for provider in load_matrix():
        assert (
            f"\n./bin/orchestra install --only {provider.id}\n" in section
        ), provider.id
        if provider.profile:
            assert (
                f"\nnpx skills add -a {provider.profile}\n" in section
            ), provider.profile


def test_dry_run_is_documented_first():
    section = _section()
    assert "### Dry run first" in section
    dry_run = section.index("./bin/orchestra install --all --dry-run")
    first_host = section.index("./bin/orchestra install --only")
    assert dry_run < first_host


def test_scope_and_flags_are_documented():
    section = _section()
    assert "### Scope and flags" in section
    for flag in DOCUMENTED_FLAGS:
        assert flag in section, flag
    for example in ("--copy", "--global", "--uninstall"):
        assert f"./bin/orchestra install --only claude {example}" in section, example


def test_documented_flags_exist_in_the_cli():
    proc = subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "install", "--help"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    for flag in DOCUMENTED_FLAGS:
        assert flag in proc.stdout, flag


def test_agent_skills_section_documents_every_generated_skill():
    section = _agent_skills_section()
    skills = _generated_skills()
    for skill in skills:
        assert f"`{skill}`" in section, skill
    assert "references/" in section
    assert "two levels above" not in section


def test_agent_skills_section_points_at_the_cli_install():
    section = _agent_skills_section()
    assert "npx skills add -a" in section
    assert "Install with the CLI" in section


def test_quick_start_uses_the_console_script_for_checks():
    text = _readme()
    quick_start = text[: text.index("## Kinds")]
    assert "orchestra check --acceptance" in quick_start
    assert "bin/orchestra check" not in text


def test_cli_section_lists_the_current_subcommands():
    section = _section_of("## CLI")
    for command in DOCUMENTED_COMMANDS:
        assert f"`{command}`" in section, command

    proc = subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "--help"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    for command in DOCUMENTED_COMMANDS:
        assert command in proc.stdout, command
