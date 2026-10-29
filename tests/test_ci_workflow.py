import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"
CI = WORKFLOWS / "ci.yml"
TEST_JOBS = ("test-canon", "test-tuner", "test-orchestra", "test-tmux")


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


def test_r11_checks_runs_canon_validate():
    assert any("canon validate" in line for line in run_lines("checks"))


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
        and "-m tmux" not in line
        for line in all_run_lines()
    )


def test_r18_tmux_job_installs_tmux():
    assert any(
        "apt-get install" in line and "tmux" in line for line in run_lines("test-tmux")
    )


def test_r19_tmux_job_runs_tmux_marker_without_xdist():
    lines = [line for line in run_lines("test-tmux") if "pytest" in line]
    assert lines
    for line in lines:
        assert "-m tmux" in line
        assert not re.search(r"(^|\s)-n(\s|$)", line)


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


def test_r22_types_job_runs_mypy_with_continue_on_error():
    spec = job("types")
    assert any("mypy" in line for line in run_lines("types"))
    assert spec.get("continue-on-error") is True


def test_blocking_jobs_do_not_continue_on_error():
    for name, spec in jobs().items():
        if name == "types":
            continue
        assert not spec.get("continue-on-error"), name
        for step in spec.get("steps", []):
            assert not step.get("continue-on-error"), name


def test_no_run_step_ends_with_or_true():
    for line in all_run_lines():
        assert not line.rstrip().endswith("|| true"), line
