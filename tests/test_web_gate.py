import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from test_ci_workflow import ROOT, WEB_DIR, job, run_lines

UI = ROOT / WEB_DIR
NPM = shutil.which("npm")
needs_npm = pytest.mark.skipif(NPM is None, reason="npm is not on PATH")
EXACT_VERSION = re.compile(r"^\d+\.\d+\.\d+$")
AGENTS = ROOT / "AGENTS.md"


def _ui_copy(tmp_path: Path, link_modules: bool = True) -> Path:
    dest = tmp_path / "ui"
    shutil.copytree(UI, dest, ignore=shutil.ignore_patterns("node_modules", "dist"))
    if link_modules and (UI / "node_modules").is_dir():
        (dest / "node_modules").symlink_to(UI / "node_modules")
    elif link_modules:
        installed = _npm(dest, "ci", "--no-audit", "--no-fund")
        assert installed.returncode == 0, _output(installed)
    return dest


def _npm(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["npm", *args], cwd=cwd, capture_output=True, text=True, check=False)


def _output(result: subprocess.CompletedProcess) -> str:
    return result.stdout + result.stderr


def _ts_svelte_section() -> str | None:
    lines = AGENTS.read_text().splitlines()
    for start, line in enumerate(lines):
        lowered = line.lower()
        if line.startswith("#") and "typescript" in lowered and "svelte" in lowered:
            level = len(line) - len(line.lstrip("#"))
            body = []
            for rest in lines[start + 1 :]:
                if rest.startswith("#") and len(rest) - len(rest.lstrip("#")) <= level:
                    break
                body.append(rest)
            return "\n".join(body)
    return None


@needs_npm
def test_r3_type_error_fails_check(tmp_path):
    ui = _ui_copy(tmp_path)
    control = _npm(ui, "run", "check")
    assert control.returncode == 0, _output(control)

    (ui / "src" / "gate_type_error.ts").write_text(
        'export const broken: number = "not a number";\n'
    )
    broken = _npm(ui, "run", "check")
    assert broken.returncode != 0, "npm run check passed despite a type error"


@needs_npm
def test_r4_error_and_warning_findings_fail_lint(tmp_path):
    ui = _ui_copy(tmp_path)
    control = _npm(ui, "run", "lint")
    assert control.returncode == 0, _output(control)

    finding = ui / "src" / "gate_lint_finding.ts"
    finding.write_text("export function gate() {\n  debugger;\n}\n")
    error = _npm(ui, "run", "lint")
    assert error.returncode != 0, "npm run lint passed despite an error finding"

    finding.write_text("export function gate(value: any) {\n  return value;\n}\n")
    warning = _npm(ui, "run", "lint")
    assert warning.returncode != 0, "npm run lint passed despite a warning finding"


def test_r5_biome_has_an_exact_version():
    package = json.loads((UI / "package.json").read_text())
    version = package.get("devDependencies", {}).get("@biomejs/biome")
    assert version is not None, "@biomejs/biome is not a devDependency"
    assert EXACT_VERSION.match(version), f"@biomejs/biome is not pinned: {version}"


def test_r6_biome_json_enables_full_svelte_support():
    config = UI / "biome.json"
    assert config.is_file(), "missing biome.json"
    html = json.loads(config.read_text()).get("html", {})
    assert html.get("experimentalFullSupportEnabled") is True


def test_r8_agents_md_has_a_ts_svelte_section():
    assert _ts_svelte_section() is not None, "AGENTS.md has no TypeScript and Svelte heading"


def test_r9_agents_md_section_names_the_three_commands():
    section = _ts_svelte_section()
    assert section is not None, "AGENTS.md has no TypeScript and Svelte heading"
    for command in ("npm run lint", "npm run check", "npm test"):
        assert command in section, f"TypeScript and Svelte section omits {command}"


@needs_npm
def test_web_job_run_lines_pass(tmp_path):
    assert job("web"), "ci.yml has no web job"
    lines = run_lines("web")
    assert lines, "web job has no run lines"
    copy = _ui_copy(tmp_path, link_modules=False)
    for line in lines:
        result = subprocess.run(
            line, shell=True, cwd=copy, capture_output=True, text=True, check=False
        )
        assert result.returncode == 0, f"{line}\n{_output(result)}"
