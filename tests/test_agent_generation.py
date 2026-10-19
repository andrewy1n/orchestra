"""One canonical reviewer prompt, rendered into each host's frontmatter.

``agents/reviewer.prompt.md`` carries the prompt and the restriction set.
These tests prove the per-host files keep that body byte-for-byte and only
change the frontmatter keys their harness understands (R13). The checkout's
``agents/se-reviewer.md`` is a generated copy of the Claude rendering, not a
second authored prompt, and a drift check keeps it that way.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from installer import agents

REPO_ROOT = Path(__file__).resolve().parents[1]
MARKER = ".orchestra-install.json"
BUILD = REPO_ROOT / "scripts" / "build_skills.py"
GENERATED_AGENT = REPO_ROOT / "agents" / "se-reviewer.md"


def split_frontmatter(text: str) -> tuple[str, str]:
    assert text.startswith("---\n"), text[:40]
    header, _, body = text[4:].partition("\n---\n")
    assert header, "empty frontmatter"
    return header, body.lstrip("\n")


def run_install(
    *args: str, source: Path, home: Path
) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(REPO_ROOT), env.get("PYTHONPATH", "")]
    ).strip(os.pathsep)
    env["ORCHESTRA_INSTALL_SOURCE"] = str(source)
    env["HOME"] = str(home)
    affidavit_checkout = Path(os.environ.get("AFFIDAVIT_ROOT", Path.home() / "affidavit"))
    if (affidavit_checkout / "affidavit" / "__init__.py").is_file():
        env.setdefault("AFFIDAVIT_ROOT", str(affidavit_checkout))
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "install", *args],
        cwd=str(home.parent),
        env=env,
        capture_output=True,
        text=True,
    )


def test_canonical_prompt_declares_one_restriction_set():
    agent = agents.load(REPO_ROOT)
    assert agent.name == "se-reviewer"
    assert agent.mode == "subagent"
    assert agent.tools == ("Read", "Grep", "Glob", "Bash")
    assert {"Write", "Edit"} <= set(agent.deny)
    assert agent.store_writes is False
    assert "no store records" in agent.body


def test_claude_rendering_uses_the_canonical_tools_allowlist():
    header, body = split_frontmatter(
        agents.render("claude", agents.load(REPO_ROOT))
    )
    assert "name: se-reviewer" in header
    assert "tools: Read, Grep, Glob, Bash" in header
    assert "Write" not in header
    assert "Edit" not in header
    assert body == agents.load(REPO_ROOT).body


def test_opencode_rendering_is_a_subagent_with_denied_writes():
    header, body = split_frontmatter(
        agents.render("opencode", agents.load(REPO_ROOT))
    )
    assert "mode: subagent" in header
    assert "permissions:" in header
    assert "  read: allow" in header
    assert "  edit: deny" in header
    assert "  write: deny" in header
    assert body == agents.load(REPO_ROOT).body


def test_cursor_rendering_is_read_only():
    header, body = split_frontmatter(
        agents.render("cursor", agents.load(REPO_ROOT))
    )
    assert "readonly: true" in header
    assert body == agents.load(REPO_ROOT).body


def test_every_host_body_is_the_canonical_body():
    canonical = agents.load(REPO_ROOT)
    rendered = agents.render_all(REPO_ROOT)
    assert set(rendered) == {"claude", "cursor", "opencode"}
    for provider_id, text in rendered.items():
        _, body = split_frontmatter(text)
        assert body == canonical.body, provider_id


def test_checkout_agent_file_is_the_claude_rendering():
    """The tracked ``agents/se-reviewer.md`` is generated, not authored."""
    assert GENERATED_AGENT.is_file(), f"{GENERATED_AGENT} is missing"
    assert GENERATED_AGENT.read_text(encoding="utf-8") == agents.render(
        "claude", agents.load(REPO_ROOT)
    )


def test_checkout_agent_file_carries_the_canonical_body():
    canonical = agents.load(REPO_ROOT)
    header, body = split_frontmatter(GENERATED_AGENT.read_text(encoding="utf-8"))
    assert body == canonical.body
    assert "name: se-reviewer" in header
    assert "tools: Read, Grep, Glob, Bash" in header
    assert "mode:" not in header


def run_build(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(BUILD), "--root", str(root)],
        capture_output=True,
        text=True,
    )


def authored_tree(tmp_path: Path) -> Path:
    for name in ("agents", "shared", "skills"):
        shutil.copytree(REPO_ROOT / name, tmp_path / name)
    return tmp_path


def test_generated_agent_drift_is_detected(tmp_path):
    root = authored_tree(tmp_path)
    built = run_build(root)
    assert built.returncode == 0, built.stdout + built.stderr

    clean = subprocess.run(
        [sys.executable, str(BUILD), "--root", str(root), "--check"],
        capture_output=True,
        text=True,
    )
    assert clean.returncode == 0, clean.stdout + clean.stderr

    target = root / "agents" / "se-reviewer.md"
    target.write_text(target.read_text(encoding="utf-8") + "\nhand edit\n")
    drifted = subprocess.run(
        [sys.executable, str(BUILD), "--root", str(root), "--check"],
        capture_output=True,
        text=True,
    )
    assert drifted.returncode != 0
    assert "drift" in (drifted.stdout + drifted.stderr).lower()
    assert "se-reviewer.md" in (drifted.stdout + drifted.stderr)


def test_editing_the_canonical_prompt_changes_the_generated_agent(tmp_path):
    root = authored_tree(tmp_path)
    canonical = root / "agents" / "reviewer.prompt.md"
    canonical.write_text(
        canonical.read_text(encoding="utf-8").replace(
            "tools: Read, Grep, Glob, Bash", "tools: Read, Grep, Glob"
        ),
        encoding="utf-8",
    )
    stale = subprocess.run(
        [sys.executable, str(BUILD), "--root", str(root), "--check"],
        capture_output=True,
        text=True,
    )
    assert stale.returncode != 0
    built = run_build(root)
    assert built.returncode == 0, built.stdout + built.stderr
    header, _ = split_frontmatter(
        (root / "agents" / "se-reviewer.md").read_text(encoding="utf-8")
    )
    assert "tools: Read, Grep, Glob" in header
    assert "Bash" not in header


def test_generated_agent_is_installed_for_each_native_host(tmp_path):
    home = tmp_path / "home"
    for provider_id in ("claude", "cursor", "opencode"):
        proc = run_install(
            "--only", provider_id, "--home", str(home), "--copy",
            source=REPO_ROOT, home=home,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        installed = home / f".{provider_id}" / "agents" / "se-reviewer.md"
        assert installed.is_file(), provider_id
        assert installed.read_text(encoding="utf-8") == agents.render(
            provider_id, agents.load(REPO_ROOT)
        ), provider_id
        assert (home / f".{provider_id}" / MARKER).is_file()


def test_extending_the_canonical_tools_changes_every_host(tmp_path):
    source = tmp_path / "source"
    (source / "agents").mkdir(parents=True)
    (source / "skills" / "init").mkdir(parents=True)
    (source / "skills" / "init" / "SKILL.md").write_text(
        "---\nname: init\ndescription: fixture\n---\n", encoding="utf-8"
    )
    canonical = (REPO_ROOT / "agents" / "reviewer.prompt.md").read_text(
        encoding="utf-8"
    )
    (source / "agents" / "reviewer.prompt.md").write_text(
        canonical.replace(
            "tools: Read, Grep, Glob, Bash", "tools: Read, Grep, Glob"
        ),
        encoding="utf-8",
    )
    for provider_id in ("claude", "opencode"):
        header, _ = split_frontmatter(agents.render(provider_id, agents.load(source)))
        assert "Bash" not in header, provider_id
        if provider_id == "claude":
            assert "tools: Read, Grep, Glob" in header
            assert "Bash" not in header


def test_missing_canonical_prompt_still_installs_without_an_agent(tmp_path):
    source = tmp_path / "source"
    (source / "skills" / "init").mkdir(parents=True)
    (source / "skills" / "init" / "SKILL.md").write_text(
        "---\nname: init\ndescription: fixture\n---\n", encoding="utf-8"
    )
    home = tmp_path / "home"
    proc = run_install(
        "--only", "claude", "--home", str(home), "--copy",
        source=source, home=home,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (home / ".claude" / "skills" / "init" / "SKILL.md").is_file()
    assert not (home / ".claude" / "agents" / "se-reviewer.md").exists()
    assert "verified: ok" in proc.stdout
