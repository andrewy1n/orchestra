"""Orchestra skills name record versus bind. Aff stays mode-free.

``verify-work`` says when to record an evidence-observation versus when
to ``aff bind`` that observation to a claim. ``execute-phase`` says when
bind or recheck is required before a manifest claim is earned. A
documented path shows claim → evidence-binding → evidence-observation.
No aff work-kind, mode flag, or policy switch encodes that choice.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from conftest import REPO_ROOT

SKILLS = REPO_ROOT / "skills"
EXECUTE = SKILLS / "execute-phase" / "SKILL.md"
VERIFY = SKILLS / "verify-work" / "SKILL.md"

_AFFIDAVIT_ROOT = Path(
    os.environ.get("AFFIDAVIT_ROOT", str(Path.home() / "affidavit"))
).expanduser()

_AFF_SWITCH = re.compile(
    r"record-versus-bind|record_versus_bind|record-vs-bind|record_vs_bind|--mode\b|--policy\b"
)
_SECTION = re.compile(r"record versus bind|record vs\.? bind", re.I)
_AFF_BIND = re.compile(r"(?<![\w.-])aff bind\b")
_AFF_RECHECK = re.compile(r"(?<![\w.-])aff recheck\b")
_AFF_TRAIL = re.compile(r"(?<![\w.-])aff trail\b")
_LINKAGE = re.compile(
    r"claim(?:[-\s]+id)?>?\s*(?:→|->)\s*<?evidence-binding(?:-id)?>?"
    r"\s*(?:→|->)\s*<?evidence-observation(?:-id)?>?",
    re.I,
)

_MODE_PATTERNS = (
    ("aff --mode", re.compile(r"(?<![\w.-])aff\s+--mode\b", re.I)),
    ("aff --mode", re.compile(r"(?<![\w.-])aff\s+\S+\s+--mode\b", re.I)),
    (
        "--record-versus-bind",
        re.compile(r"--record-versus-bind\b|--record-vs-bind\b", re.I),
    ),
    (
        "aff record-versus-bind",
        re.compile(r"(?<![\w.-])aff\s+record-versus-bind\b", re.I),
    ),
    (
        "aff record-versus-bind",
        re.compile(r"(?<![\w.-])aff\s+record-vs-bind\b", re.I),
    ),
    (
        "work-kind record-versus-bind",
        re.compile(r"work-kind\b[^\n]{0,160}record-versus-bind\b", re.I),
    ),
)

_FORBIDDEN_FIXTURE = """\
```bash
aff --mode record --cwd <repo-or-worktree>
aff verdict --mode bind --claim <claim-id>
aff record-versus-bind --cwd <repo-or-worktree>
```

The work-kind `record-versus-bind` selects record versus bind.
"""

_ALLOWED_FIXTURE = """\
## Record versus bind

Techniques and audit may record an unbound evidence-observation.
Earning a manifest claim requires `aff bind` (and `aff recheck` when
the binding must be judged again) before treating that manifest claim
as earned. Inspect what was recorded with `aff trail`.

claim → evidence-binding → evidence-observation
"""


def invented_aff_mode_violations(text: str) -> list[str]:
    """Aff invocations that invent a record-versus-bind mode or work-kind."""
    found: list[str] = []
    seen: set[str] = set()
    for label, pattern in _MODE_PATTERNS:
        if label not in seen and pattern.search(text):
            seen.add(label)
            found.append(label)
    return found


def scan_skills(skills_root: Path) -> list[str]:
    violations: list[str] = []
    for path in sorted(skills_root.rglob("*.md")):
        for item in invented_aff_mode_violations(path.read_text()):
            violations.append(f"{path.relative_to(skills_root)}: {item}")
    return violations


def _window_has(text: str, patterns: list[re.Pattern[str]], span: int = 800) -> bool:
    if not patterns:
        return False
    for match in patterns[0].finditer(text):
        start = max(0, match.start() - span)
        end = min(len(text), match.end() + span)
        window = text[start:end]
        if all(pattern.search(window) for pattern in patterns[1:]):
            return True
    return False


def missing_record_versus_bind(text: str) -> list[str]:
    """Gaps in when to record an evidence-observation versus when to aff bind."""
    missing: list[str] = []
    if not _SECTION.search(text):
        missing.append("section 'Record versus bind'")
    record_terms = [
        re.compile(r"techniques?|audit", re.I),
        re.compile(r"\brecord(?:ed|ing|s)?\b|\bleave\b", re.I),
        re.compile(r"unbound", re.I),
        re.compile(r"(?:evidence-)?observations?", re.I),
    ]
    if not _window_has(text, record_terms):
        missing.append(
            "when techniques or audit record an unbound evidence-observation"
        )
    bind_terms = [
        _AFF_BIND,
        re.compile(r"observations?|claim", re.I),
    ]
    if not _window_has(text, bind_terms, span=400):
        missing.append("when to `aff bind` an observation to a claim")
    if not _AFF_TRAIL.search(text):
        missing.append("`aff trail`")
    return missing


def missing_earned_rule(text: str) -> list[str]:
    """Gaps in when bind or recheck is required before a claim is earned."""
    missing: list[str] = []
    if not _AFF_BIND.search(text):
        missing.append("`aff bind`")
    if not _AFF_RECHECK.search(text):
        missing.append("`aff recheck`")
    earned = re.compile(r"earn(?:ed|ing)?", re.I)
    if not _window_has(text, [_AFF_BIND, earned], span=400) and not _window_has(
        text, [_AFF_RECHECK, earned], span=400
    ):
        missing.append(
            "bind or recheck required before treating a manifest claim as earned"
        )
    return missing


def skill_linkage_paths() -> list[Path]:
    found: list[Path] = []
    for path in (VERIFY, EXECUTE):
        text = path.read_text()
        if _LINKAGE.search(text) and _AFF_BIND.search(text):
            found.append(path)
    return found


def _subparsers(help_text: str) -> list[str]:
    """Argparse subparsers render as ``{a,b} ...``. Positional choices do not."""
    names: list[str] = []
    for group in re.findall(r"\{([^}]+)\}\s+\.\.\.", help_text):
        for name in group.split(","):
            name = name.strip()
            if name and not name.startswith("-"):
                names.append(name)
    return names


def _collect_aff_help(binary: Path) -> str:
    seen: set[tuple[str, ...]] = set()
    chunks: list[str] = []

    def walk(args: tuple[str, ...]) -> None:
        if args in seen:
            return
        seen.add(args)
        result = subprocess.run(
            [sys.executable, str(binary), *args, "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        chunks.append(result.stdout)
        for name in _subparsers(result.stdout):
            walk((*args, name))

    walk(())
    return "\n".join(chunks)


def aff_policy_switches() -> list[str]:
    """Work-kind, mode flag, or policy switch that encodes record-versus-bind."""
    hits: list[str] = []
    for rel in ("affidavit/cli.py", "affidavit/evidence_kind.py"):
        text = (_AFFIDAVIT_ROOT / rel).read_text()
        for token in sorted(set(_AFF_SWITCH.findall(text))):
            hits.append(f"{rel}: {token}")
    help_text = _collect_aff_help(_AFFIDAVIT_ROOT / "bin" / "aff")
    for token in sorted(set(_AFF_SWITCH.findall(help_text))):
        hits.append(f"aff --help: {token}")
    return hits


def policy_gaps() -> list[str]:
    gaps: list[str] = []
    record = missing_record_versus_bind(VERIFY.read_text())
    if record:
        gaps.append("verify-work missing: " + "; ".join(record))
    earned = missing_earned_rule(EXECUTE.read_text())
    if earned:
        gaps.append("execute-phase missing: " + "; ".join(earned))
    if not skill_linkage_paths():
        gaps.append(
            "no verify-work or execute-phase path shows "
            "claim → evidence-binding → evidence-observation"
        )
    return gaps


def test_verify_work_names_when_to_record_an_observation_versus_aff_bind():
    missing = missing_record_versus_bind(VERIFY.read_text())
    assert not missing, "verify-work missing: " + "; ".join(missing)


def test_execute_phase_names_when_bind_or_recheck_before_a_claim_is_earned():
    missing = missing_earned_rule(EXECUTE.read_text())
    assert not missing, "execute-phase missing: " + "; ".join(missing)


def test_verify_or_execute_skill_shows_claim_binding_observation_linkage():
    found = skill_linkage_paths()
    assert found, (
        "verify-work or execute-phase must show "
        "claim → evidence-binding → evidence-observation "
        "on a path that also runs `aff bind`"
    )


def test_aff_has_no_record_versus_bind_mode_and_policy_lives_in_skills():
    problems = [f"aff encodes record-versus-bind via {item}" for item in aff_policy_switches()]
    problems.extend(scan_skills(SKILLS))
    problems.extend(policy_gaps())
    assert not problems, "\n".join(problems)


def test_fixture_skill_inventing_an_aff_mode_fails_the_scanner(tmp_path: Path):
    bad_root = tmp_path / "bad"
    bad = bad_root / "skills" / "bad" / "SKILL.md"
    bad.parent.mkdir(parents=True)
    bad.write_text(_FORBIDDEN_FIXTURE)
    violations = scan_skills(bad_root / "skills")
    assert any("aff --mode" in item for item in violations)
    assert any("aff record-versus-bind" in item for item in violations)
    assert any("work-kind record-versus-bind" in item for item in violations)

    ok_root = tmp_path / "ok"
    ok = ok_root / "skills" / "ok" / "SKILL.md"
    ok.parent.mkdir(parents=True)
    ok.write_text(_ALLOWED_FIXTURE)
    assert scan_skills(ok_root / "skills") == []


def test_live_skills_pass_the_scanner_when_policy_is_present():
    problems = scan_skills(SKILLS)
    problems.extend(policy_gaps())
    assert not problems, "\n".join(problems)
