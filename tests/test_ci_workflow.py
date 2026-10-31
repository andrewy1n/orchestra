import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"
CI = WORKFLOWS / "ci.yml"
TEST_JOBS = ("test-canon", "test-tuner", "test-orchestra")


def load():
    assert CI.is_file(), "missing .github/workflows/ci.yml"
    yaml = pytest.importorskip("yaml")
    data = yaml.safe_load(CI.read_text())
    assert isinstance(data, dict), "ci.yml is not a mapping"
    return data


def triggers():
    return load()[True]


def jobs():
    return load()["jobs"]


def job(name):
    found = jobs()
    assert name in found, f"missing job {name}"
    return found[name]


def run_lines(name):
    lines = []
    for step in job(name).get("steps", []):
        if "run" in step:
            lines.extend(
                line.strip() for line in step["run"].splitlines() if line.strip()
            )
    return lines


def all_run_lines():
    return [line for name in jobs() for line in run_lines(name)]


def uses_uv(name):
    return any(
        "uv" in line.split() or line.startswith(("uv ", "uvx "))
        for line in run_lines(name)
    ) or any(
        str(step.get("uses", "")).startswith("astral-sh/setup-uv")
        for step in job(name).get("steps", [])
    )


def runs_only_npm(name):
    lines = run_lines(name)
    return bool(lines) and all(line.startswith("npm ") for line in lines)


def setup_uv_steps(name):
    return [
        step
        for step in job(name).get("steps", [])
        if str(step.get("uses", "")).startswith("astral-sh/setup-uv")
    ]


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)


def _verdict_base() -> str:
    for ref in ("origin/main", "main"):
        base = _git("merge-base", ref, "HEAD")
        if base.returncode == 0 and base.stdout.strip():
            return base.stdout.strip()
    return "HEAD"


def test_r1_workflow_exists_and_tuner_verdict_unchanged():
    assert CI.is_file(), "missing .github/workflows/ci.yml"
    verdict = WORKFLOWS / "tuner-verdict.yml"
    assert verdict.is_file()
    base = _verdict_base()
    diff = _git("diff", "--quiet", base, "--", str(verdict))
    assert diff.returncode == 0, f"tuner-verdict.yml differs from {base}"


def test_r2_runs_on_push_to_main():
    assert "main" in triggers()["push"]["branches"]


def test_r3_runs_on_push_to_phase_branches():
    assert "phase/**" in triggers()["push"]["branches"]


def test_r4_runs_on_pull_request():
    assert "pull_request" in triggers()


def test_r5_runs_on_workflow_dispatch():
    assert "workflow_dispatch" in triggers()


def test_r6_concurrency_cancels_in_progress():
    concurrency = load().get("concurrency")
    assert isinstance(concurrency, dict), "missing top-level concurrency"
    assert concurrency.get("group")
    assert concurrency.get("cancel-in-progress") is True


def test_r7_every_job_sets_timeout_minutes():
    found = jobs()
    assert found
    for name, spec in found.items():
        assert "timeout-minutes" in spec, f"{name} has no timeout-minutes"


def test_r8_every_job_runs_python_3_10():
    found = jobs()
    assert found
    for name in found:
        if not setup_uv_steps(name) and runs_only_npm(name):
            continue
        versions = [
            str(step.get("with", {}).get("python-version"))
            for step in setup_uv_steps(name)
        ]
        assert versions, f"{name} has no setup-uv step"
        assert all(v == "3.10" for v in versions), f"{name} python-version {versions}"


def test_r9_checks_runs_build_skills_check():
    assert any(
        "scripts/build_skills.py --check" in line for line in run_lines("checks")
    )


def test_r10_checks_runs_plugin_name_check():
    assert any(
        "scripts/check_orchestra_plugin_names.py" in line for line in run_lines("checks")
    )


def test_r11_ci_does_not_read_or_validate_the_live_store():
    assert not any("canon validate" in line for line in all_run_lines())


def test_r12_checks_runs_ruff_check_with_pinned_version():
    assert any(
        re.search(r"ruff(==|@)\d+\.\d+\.\d+\b.*\bcheck\b", line)
        or re.search(r"\bcheck\b.*ruff(==|@)\d+\.\d+\.\d+", line)
        for line in run_lines("checks")
    )


def test_r15_runs_canon_tests():
    assert any(
        "pytest" in line
        and "-n auto" in line
        and "--confcutdir=tests/canon" in line
        and line.endswith("tests/canon")
        for line in all_run_lines()
    )


def test_r16_runs_tuner_tests():
    assert any(
        "pytest" in line
        and "-n auto" in line
        and "--confcutdir=tests/tuner" in line
        and line.endswith("tests/tuner")
        for line in all_run_lines()
    )


def test_r17_runs_remaining_tests():
    assert any(
        "pytest" in line
        and "-n auto" in line
        and "tests --ignore=tests/canon --ignore=tests/tuner" in line
        for line in all_run_lines()
    )


def test_r20_test_jobs_do_not_need_each_other():
    found = jobs()
    for name in TEST_JOBS:
        assert name in found, f"missing job {name}"
        needs = found[name].get("needs") or []
        if isinstance(needs, str):
            needs = [needs]
        assert not set(needs) & set(TEST_JOBS), f"{name} needs {needs}"


def test_r21_uv_jobs_enable_cache():
    found = jobs()
    assert found
    for name in found:
        if not uses_uv(name):
            continue
        steps = setup_uv_steps(name)
        assert steps, f"{name} has no setup-uv step"
        for step in steps:
            assert step.get("with", {}).get("enable-cache") is True, name


def test_mypy_gate_r9_types_job_runs_basedpyright():
    assert any("uv run basedpyright" in line for line in run_lines("types"))


def test_mypy_gate_r10_types_job_is_blocking():
    assert not job("types").get("continue-on-error")


def test_mypy_gate_r11_types_steps_do_not_continue_on_error():
    steps = job("types").get("steps", [])
    checks = [step for step in steps if "basedpyright" in str(step.get("run", ""))]
    assert checks, "types job has no basedpyright step"
    for step in steps:
        assert not step.get("continue-on-error"), step


def test_mypy_gate_r12_no_job_runs_mypy():
    for name in jobs():
        for line in run_lines(name):
            assert "mypy" not in line, f"{name}: {line}"


def test_blocking_jobs_do_not_continue_on_error():
    for name, spec in jobs().items():
        assert not spec.get("continue-on-error"), name
        for step in spec.get("steps", []):
            assert not step.get("continue-on-error"), name


def test_no_run_step_ends_with_or_true():
    for line in all_run_lines():
        assert not line.rstrip().endswith("|| true"), line


def test_wheel_smoke_r1_wheel_job_exists():
    assert "wheel" in jobs()


def test_wheel_smoke_r2_wheel_job_is_blocking():
    assert not job("wheel").get("continue-on-error")


def test_wheel_smoke_r3_wheel_steps_do_not_continue_on_error():
    steps = job("wheel").get("steps") or []
    assert isinstance(steps, list), "wheel job steps are not a list"
    for step in steps:
        assert isinstance(step, dict), step
        assert not step.get("continue-on-error"), step


def test_wheel_smoke_r4_wheel_job_runs_script():
    assert "python3 scripts/wheel_smoke.py" in run_lines("wheel")


WEB_DIR = "dashboard/frontend"
WEB_COMMANDS = ("npm ci", "npm run lint", "npm run check", "npm test", "npm run build")


def _web_steps():
    spec = job("web")
    default_dir = spec.get("defaults", {}).get("run", {}).get("working-directory")
    pairs = []
    for step in spec.get("steps", []):
        if "run" not in step:
            continue
        workdir = step.get("working-directory", default_dir)
        for line in step["run"].splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("cd ") and line[3:].strip().rstrip("/") == WEB_DIR:
                workdir = WEB_DIR
                continue
            pairs.append((line, workdir))
    return pairs


def test_r1_web_job_runs_the_five_commands_in_order():
    pairs = _web_steps()
    commands = [line for line, _ in pairs]
    positions = []
    for command in WEB_COMMANDS:
        assert command in commands, f"web job does not run {command}"
        positions.append(commands.index(command))
    assert positions == sorted(positions), f"web commands out of order: {commands}"
    for command in WEB_COMMANDS:
        workdir = dict(pairs)[command]
        assert workdir is not None and workdir.rstrip("/") == WEB_DIR, (
            f"{command} runs in {workdir}"
        )


def test_r2_web_job_has_no_path_filter():
    spec = job("web")
    assert "if" not in spec, "web job has a job-level if"
    on = triggers()
    for key in ("push", "pull_request"):
        assert key in on, f"web job does not run on {key}"
        trigger = on[key] or {}
        assert "paths" not in trigger, f"{key} trigger has paths"
        assert "paths-ignore" not in trigger, f"{key} trigger has paths-ignore"
