from __future__ import annotations

import inspect
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

import orchestra.canon.extensions as extensions
from evals.seeded_defects.cases import load_case_set
from orchestra.conductor.verification.review import review_brief

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "orchestra"


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)


def _plugin(entry_name: str, entry_value: str) -> SimpleNamespace:
    entries = (
        SimpleNamespace(name=entry_name, value=entry_value, group=extensions.PLUGIN_API_GROUP),
        SimpleNamespace(name="demo", value="{}", group=extensions.PLUGIN_CONFIG_GROUP),
    )
    return SimpleNamespace(
        name="demo",
        value="demo:Plugin",
        dist=SimpleNamespace(metadata={"Name": "demo-dist"}, version="1.0.0", entry_points=entries),
        load=lambda: "loaded",
    )


def _install(monkeypatch: pytest.MonkeyPatch, plugin: SimpleNamespace) -> None:
    def discover(*, group: str) -> tuple[SimpleNamespace, ...]:
        return (plugin,) if group == "orchestra.tuner.verify" else ()

    monkeypatch.setattr(extensions.metadata, "entry_points", discover)


def test_seeded_defect_cases_match_origin_main() -> None:
    result = _git("diff", "--name-only", "origin/main", "--", "evals/seeded_defects/cases")

    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == []


def test_real_seeded_defect_cases_load_against_repo_history() -> None:
    cases = load_case_set(ROOT / "evals" / "seeded_defects" / "cases", ROOT)

    assert cases


def test_oracle_freeze_shim_is_deleted() -> None:
    assert not (PACKAGE / "conductor/verification/evidence/oracle_freeze.py").exists()


def test_review_brief_requires_suite_readiness_argument() -> None:
    parameter = inspect.signature(review_brief.build_review_brief).parameters.get("suite_refusal")

    assert parameter is not None
    assert parameter.default is inspect.Parameter.empty


def test_review_brief_is_refused_without_ready_suite() -> None:
    with pytest.raises(RuntimeError, match="suite not ready"):
        review_brief.build_review_brief(
            SimpleNamespace(),  # pyright: ignore[reportArgumentType]
            ROOT,
            base="a",
            phase_head="b",
            phase="p",
            suite_refusal="suite not ready",
        )


def test_plugin_v1_entry_is_rejected_naming_supported_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install(monkeypatch, _plugin("v1", "module:obj"))

    with pytest.raises(extensions.PluginCatalogError, match=r"supported version is '2'"):
        extensions.resolve_plugin("tuner.verify", "demo")


def test_plugin_v2_entry_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, _plugin("v2", "module:obj"))

    registration = extensions.resolve_plugin("tuner.verify", "demo")

    assert registration.descriptor.api_version == "2"
    assert registration.load() == "loaded"


def test_plugin_version_named_entry_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, _plugin("version", "2"))

    with pytest.raises(extensions.PluginCatalogError):
        extensions.resolve_plugin("tuner.verify", "demo")


def test_plugin_docs_state_only_supported_api_version() -> None:
    text = (ROOT / "docs" / "plugins.md").read_text(encoding="utf-8")

    assert "other than `1`" not in text
    assert re.search(r"API versions other than `2`", text)


def test_github_tool_errors_are_tool_neutral() -> None:
    assert "land.config" not in (PACKAGE / "tools" / "github.py").read_text(encoding="utf-8")


def test_git_error_message_is_defined_once() -> None:
    owners = [
        path.relative_to(ROOT).as_posix()
        for path in PACKAGE.rglob("*.py")
        if re.search(r"^def _?git_error_message\(", path.read_text(encoding="utf-8"), re.MULTILINE)
    ]

    assert len(owners) == 1, owners


def test_task_verification_module_is_renamed() -> None:
    tasks = PACKAGE / "conductor" / "tasks"

    assert not (tasks / "verification.py").exists()
    assert (tasks / "verification_run.py").exists()
