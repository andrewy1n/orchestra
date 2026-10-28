"""End-to-end composer flow through installed ``orchestra`` and ``canon`` entry points."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from test_cli_packaging import (
    REPO_ROOT,
    _git_repo,
    _roadmap_section,
    _scrub_checkout,
    installed,  # noqa: F401
    run_canon,
    run_cli,
)

IDEA_TITLE = "Show a roadmap"
IDEA_SUBJECT = "show-a-roadmap"
AREA_SUBJECT = "dash"
EFFORT_SUBJECT = "roadmap-effort"
EFFORT_GOAL = "Show a roadmap in the product"


def _canon_file_list_hash(store_dir: Path) -> str:
    if not store_dir.is_dir():
        return hashlib.sha256(b"").hexdigest()
    entries = []
    for path in sorted(p for p in store_dir.rglob("*") if p.is_file()):
        stat = path.stat()
        entries.append(f"{path.relative_to(store_dir).as_posix()}:{stat.st_size}:{stat.st_mtime_ns}")
    return hashlib.sha256("\n".join(entries).encode()).hexdigest()


def _parse_json(proc) -> dict:
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


def _active_idea(env: dict[str, str], repo: Path) -> dict:
    listed = run_canon(
        env,
        repo,
        "list",
        "--type",
        "composer:idea",
        "--subject",
        IDEA_SUBJECT,
        "--exact-subject",
        "--state",
        "active",
    )
    data = _parse_json(listed)
    assert data["count"] == 1, data
    return data["records"][0]


@dataclass
class ComposerFlow:
    repo: Path
    env: dict[str, str]
    live_store_hash_before: str
    idea_after_capture: dict
    idea_after_triage: dict
    idea_after_promote: dict
    roadmap_first: str
    roadmap_second: str
    validate_stdout: str
    validate_code: int
    effort_subject: str


@pytest.fixture(scope="module")
def composer_flow(installed, tmp_path_factory) -> ComposerFlow:  # noqa: F811
    _, base_env = installed
    env = _scrub_checkout(base_env)
    live_store_hash_before = _canon_file_list_hash(REPO_ROOT / ".canon")
    repo = _git_repo(tmp_path_factory.mktemp("composer-e2e"))

    init = run_canon(env, repo, "init", "--schemas", "score,conductor,tuner,composer")
    assert init.returncode == 0, init.stdout + init.stderr

    captured = run_cli(env, repo, "idea", IDEA_TITLE)
    assert captured.returncode == 0, captured.stdout + captured.stderr
    idea_after_capture = _active_idea(env, repo)

    area = run_canon(
        env,
        repo,
        "create",
        "--type",
        "composer:area",
        "--subject",
        AREA_SUBJECT,
        "--payload",
        '{"title":"Dashboard"}',
        "--body",
        "## Scope\n\nThe dashboard.",
    )
    assert area.returncode == 0, area.stdout + area.stderr

    idea = _active_idea(env, repo)
    triaged = run_canon(
        env,
        repo,
        "supersede",
        "--type",
        "composer:idea",
        "--id",
        idea["id"],
        "--expected-revision",
        idea["revision"],
        "--payload",
        json.dumps({"area": AREA_SUBJECT}),
    )
    assert triaged.returncode == 0, triaged.stdout + triaged.stderr
    idea_after_triage = _active_idea(env, repo)

    roadmap_first_proc = run_cli(env, repo, "view", "roadmap")
    assert roadmap_first_proc.returncode == 0, roadmap_first_proc.stdout + roadmap_first_proc.stderr

    effort = run_canon(
        env,
        repo,
        "create",
        "--type",
        "score:effort",
        "--subject",
        EFFORT_SUBJECT,
        "--payload",
        json.dumps({"goal": EFFORT_GOAL, "kind": "deliver"}),
    )
    assert effort.returncode == 0, effort.stdout + effort.stderr

    position = run_canon(
        env,
        repo,
        "create",
        "--type",
        "score:position",
        "--subject",
        EFFORT_SUBJECT,
        "--payload",
        json.dumps(
            {
                "position": "Effort adopted for roadmap e2e",
                "scope": "effort",
                "effort": EFFORT_SUBJECT,
            }
        ),
    )
    assert position.returncode == 0, position.stdout + position.stderr

    idea = _active_idea(env, repo)
    promoted = run_canon(
        env,
        repo,
        "supersede",
        "--type",
        "composer:idea",
        "--id",
        idea["id"],
        "--expected-revision",
        idea["revision"],
        "--payload",
        json.dumps({"status": "promoted", "effort": EFFORT_SUBJECT}),
    )
    assert promoted.returncode == 0, promoted.stdout + promoted.stderr
    idea_after_promote = _active_idea(env, repo)

    roadmap_second_proc = run_cli(env, repo, "view", "roadmap")
    assert roadmap_second_proc.returncode == 0, roadmap_second_proc.stdout + roadmap_second_proc.stderr

    validated = run_canon(env, repo, "validate")
    assert validated.returncode == 0, validated.stdout + validated.stderr

    return ComposerFlow(
        repo=repo,
        env=env,
        live_store_hash_before=live_store_hash_before,
        idea_after_capture=idea_after_capture,
        idea_after_triage=idea_after_triage,
        idea_after_promote=idea_after_promote,
        roadmap_first=roadmap_first_proc.stdout,
        roadmap_second=roadmap_second_proc.stdout,
        validate_stdout=validated.stdout,
        validate_code=validated.returncode,
        effort_subject=EFFORT_SUBJECT,
    )


def test_r1_temporary_store_initialized(composer_flow: ComposerFlow):
    store = composer_flow.repo / ".canon"
    assert store.is_dir()
    config = json.loads((store / "config.json").read_text())
    assert config["format"] == "canon/1"
    assert "composer" in config.get("schemas", {})


def test_r2_open_idea_from_orchestra_idea(composer_flow: ComposerFlow):
    idea = composer_flow.idea_after_capture
    assert idea["subject"] == IDEA_SUBJECT
    assert idea["payload"]["status"] == "open"


def test_r3_area_assigned_via_triage_calls(composer_flow: ComposerFlow):
    idea = composer_flow.idea_after_triage
    assert idea["payload"].get("area") == AREA_SUBJECT
    assert idea["payload"]["status"] == "open"
    listed = run_canon(
        composer_flow.env,
        composer_flow.repo,
        "list",
        "--type",
        "composer:area",
        "--subject",
        AREA_SUBJECT,
        "--exact-subject",
        "--state",
        "active",
    )
    data = _parse_json(listed)
    assert data["count"] == 1
    assert data["records"][0]["payload"]["title"] == "Dashboard"


def test_r4_first_roadmap_lists_idea_under_area(composer_flow: ComposerFlow):
    dash = _roadmap_section(composer_flow.roadmap_first, AREA_SUBJECT)
    assert f"**{IDEA_SUBJECT}**" in dash


def test_r5_effort_created_via_init_calls(composer_flow: ComposerFlow):
    listed = run_canon(
        composer_flow.env,
        composer_flow.repo,
        "list",
        "--type",
        "score:effort",
        "--subject",
        composer_flow.effort_subject,
        "--exact-subject",
        "--state",
        "active",
    )
    data = _parse_json(listed)
    assert data["count"] == 1
    assert data["records"][0]["payload"] == {
        "goal": EFFORT_GOAL,
        "kind": "deliver",
    }
    position = run_canon(
        composer_flow.env,
        composer_flow.repo,
        "list",
        "--type",
        "score:position",
        "--subject",
        composer_flow.effort_subject,
        "--exact-subject",
        "--state",
        "active",
    )
    pos_data = _parse_json(position)
    assert pos_data["count"] == 1
    assert pos_data["records"][0]["payload"]["effort"] == composer_flow.effort_subject


def test_r6_idea_promoted_with_effort(composer_flow: ComposerFlow):
    idea = composer_flow.idea_after_promote
    assert idea["payload"]["status"] == "promoted"
    assert idea["payload"]["effort"] == composer_flow.effort_subject


def test_r7_second_roadmap_shows_promoted_idea_with_effort(composer_flow: ComposerFlow):
    dash = _roadmap_section(composer_flow.roadmap_second, AREA_SUBJECT)
    assert f"**{IDEA_SUBJECT}**" in dash
    line = next(line for line in dash.splitlines() if f"**{IDEA_SUBJECT}**" in line)
    assert composer_flow.effort_subject in line
    assert "promoted" in line


def test_r8_validate_reports_no_errors(composer_flow: ComposerFlow):
    assert composer_flow.validate_code == 0
    report = json.loads(composer_flow.validate_stdout)
    assert report["status"] == "valid"
    assert report["errors"] == []


def test_r9_live_store_unchanged(composer_flow: ComposerFlow):
    after = _canon_file_list_hash(REPO_ROOT / ".canon")
    assert after == composer_flow.live_store_hash_before
