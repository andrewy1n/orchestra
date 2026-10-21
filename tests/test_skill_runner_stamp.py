"""Skills must not forge tdd/check check-runs with runner aff.

R7: Orchestra skill and skill-reference text do not instruct creating
a method ``tdd`` or ``check`` check-run with ``runner`` set to ``aff``.
Runner-produced stamps come from ``orchestra check`` / ``orchestra
suite record`` and read ``orchestra``.
"""

from __future__ import annotations

from pathlib import Path

from conftest import REPO_ROOT
from skill_extraction import extract_invocations

SKILLS = REPO_ROOT / "skills"
_RUNNER_METHODS = frozenset({"tdd", "check"})

_FORBIDDEN_FIXTURE = """\
```bash
adaptive-artifacts create --type project:check-run \\
  --subject "<task-slug>" \\
  --payload '{"criterion_id":"<acceptance-id>","result":"pass","method":"tdd","runner":"aff"}'

adaptive-artifacts create --type project:check-run \\
  --subject "<phase-slug>-suite" \\
  --payload '{"criterion_id":"<phase-slug>-suite","result":"pass","method":"check","evidence_kind":"integration","runner":"aff"}'
```
"""

_ALLOWED_FIXTURE = """\
```bash
orchestra check --acceptance <acceptance-id> --cwd <repo-or-worktree>

orchestra suite record --phase "<phase-slug>" --effort "<focus>" --cwd <phase-worktree>

adaptive-artifacts create --type project:check-run \\
  --subject "<task-slug>" \\
  --payload '{"criterion_id":"<acceptance-id>","result":"pass","method":"manual","signed_by":""}'

cat > /tmp/close-request.json <<'EOF'
{
  "criteria": [
    {
      "method": "tdd",
      "check_run_id": "<green-id>",
      "red_runner": "orchestra"
    }
  ]
}
EOF
```
"""


def _payload(inv: dict) -> dict:
    payload = inv.get("payload")
    return payload if isinstance(payload, dict) else {}


def aff_runner_create_violations(text: str) -> list[str]:
    """Create of a tdd/check check-run that stamps ``runner: aff``."""
    found: list[str] = []
    for inv in extract_invocations(text):
        if inv.get("subcommand") != "create":
            continue
        if inv.get("type") != "project:check-run":
            continue
        payload = _payload(inv)
        method = payload.get("method")
        if method in _RUNNER_METHODS and payload.get("runner") == "aff":
            found.append(f"create project:check-run method {method} runner aff")
    return found


def scan_skills(skills_root: Path) -> list[str]:
    violations: list[str] = []
    for path in sorted(skills_root.rglob("*.md")):
        for item in aff_runner_create_violations(path.read_text()):
            violations.append(f"{path.relative_to(skills_root)}: {item}")
    return violations


def test_fixture_skill_forging_aff_runner_fails_the_scanner(tmp_path: Path):
    skill = tmp_path / "skills" / "bad" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(_FORBIDDEN_FIXTURE)
    violations = scan_skills(tmp_path / "skills")
    assert any("method tdd runner aff" in item for item in violations)
    assert any("method check runner aff" in item for item in violations)


def test_fixture_without_aff_runner_create_passes(tmp_path: Path):
    skill = tmp_path / "skills" / "ok" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(_ALLOWED_FIXTURE)
    assert scan_skills(tmp_path / "skills") == []


def test_live_skills_pass_the_runner_stamp_scanner():
    violations = scan_skills(SKILLS)
    assert not violations, "\n".join(violations)
