from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from test_boundaries import boundary_violations
from test_cli_packaging import cli_env, install_cli

REPO_ROOT = Path(__file__).resolve().parents[1]
CANON_CMD = [sys.executable, "-m", "orchestra.canon"]
BASE_SCHEMAS = (
    REPO_ROOT / "orchestra" / "score" / "schemas" / "score.json",
    REPO_ROOT / "orchestra" / "conductor" / "schemas" / "conductor.json",
    REPO_ROOT / "orchestra" / "tuner" / "schemas" / "tuner.json",
)
COMPOSER_SCHEMA = REPO_ROOT / "orchestra" / "composer" / "schemas" / "composer.json"


def _output(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def _composer_env() -> dict[str, str]:
    env = dict(os.environ)
    paths = [str(REPO_ROOT)]
    existing = env.get("PYTHONPATH", "")
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(paths))
    env["CANON_SCHEMA_PATH"] = os.pathsep.join(
        str(path) for path in (*BASE_SCHEMAS, COMPOSER_SCHEMA)
    )
    return env


def _run_canon(root: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*CANON_CMD, "--root", str(root), *args],
        capture_output=True,
        text=True,
        env=env,
    )


def _make_git_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    init = subprocess.run(["git", "-C", str(root), "init", "-q"], capture_output=True, text=True)
    assert init.returncode == 0, _output(init)
    email = subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "test@example.com"],
        capture_output=True,
        text=True,
    )
    assert email.returncode == 0, _output(email)
    name = subprocess.run(
        ["git", "-C", str(root), "config", "user.name", "test"],
        capture_output=True,
        text=True,
    )
    assert name.returncode == 0, _output(name)
    commit = subprocess.run(
        ["git", "-C", str(root), "commit", "--allow-empty", "-qm", "init"],
        capture_output=True,
        text=True,
    )
    assert commit.returncode == 0, _output(commit)
    return root


def _init_store_with_composer(tmp_path: Path) -> tuple[Path, dict[str, str], dict[str, object]]:
    root = _make_git_repo(tmp_path)
    env = _composer_env()
    init = _run_canon(root, env, "init", "--schemas", "score,conductor,tuner,composer")
    assert init.returncode == 0, _output(init)
    return root, env, json.loads(init.stdout)


def _create_area(
    root: Path, env: dict[str, str], subject: str, body: str = "## Scope\nScope details"
) -> subprocess.CompletedProcess[str]:
    return _run_canon(
        root,
        env,
        "create",
        "--type",
        "composer:area",
        "--subject",
        subject,
        "--payload",
        json.dumps({"title": f"Area {subject}"}),
        "--body",
        body,
    )


def _create_effort(
    root: Path, env: dict[str, str], subject: str = "effort-1"
) -> subprocess.CompletedProcess[str]:
    return _run_canon(
        root,
        env,
        "create",
        "--type",
        "score:effort",
        "--subject",
        subject,
        "--payload",
        json.dumps({"goal": "Composer work", "kind": "deliver"}),
    )


def _create_phase(
    root: Path,
    env: dict[str, str],
    subject: str = "phase-1",
    effort: str = "effort-1",
) -> subprocess.CompletedProcess[str]:
    return _run_canon(
        root,
        env,
        "create",
        "--type",
        "score:phase",
        "--subject",
        subject,
        "--payload",
        json.dumps({"title": "Phase", "ordinal": 1, "effort": effort}),
        "--body",
        "## Problem\nP\n## Approach\nA\n## Exit criteria\nE",
    )


@pytest.fixture(scope="module")
def installed_prefix(tmp_path_factory):
    prefix = tmp_path_factory.mktemp("composer-prefix")
    try:
        install_cli(prefix)
    except AssertionError as exc:
        return {"prefix": prefix, "env": {}, "error": str(exc)}
    env = cli_env(prefix)
    env.pop("CANON_SCHEMA_PATH", None)
    for key in ("PATH", "PYTHONPATH"):
        env[key] = os.pathsep.join(
            part
            for part in env.get(key, "").split(os.pathsep)
            if part and not part.startswith(str(REPO_ROOT))
        )
    return {"prefix": prefix, "env": env, "error": None}


def test_module_version(tmp_path: Path):
    _, _, initialized = _init_store_with_composer(tmp_path)
    assert initialized["schemas"]["composer"] == "1.1.0"


def test_area_scope(tmp_path: Path):
    root, env, _ = _init_store_with_composer(tmp_path)
    area = _create_area(root, env, "area-1")
    assert area.returncode == 0, _output(area)


def test_area_needs_scope(tmp_path: Path):
    root, env, _ = _init_store_with_composer(tmp_path)
    valid = _create_area(root, env, "area-ok")
    assert valid.returncode == 0, _output(valid)
    invalid = _create_area(root, env, "area-no-scope", body="## Notes\nNo scope section")
    assert invalid.returncode != 0
    assert "scope" in _output(invalid).lower()


def test_placement_requires_area_ref(tmp_path: Path):
    root, env, _ = _init_store_with_composer(tmp_path)
    area = _create_area(root, env, "area-p")
    assert area.returncode == 0, _output(area)
    effort = _create_effort(root, env, "effort-p")
    assert effort.returncode == 0, _output(effort)
    valid = _run_canon(
        root,
        env,
        "create",
        "--type",
        "composer:placement",
        "--subject",
        "effort-p",
        "--payload",
        json.dumps({"area": "area-p"}),
    )
    assert valid.returncode == 0, _output(valid)
    missing = _run_canon(
        root,
        env,
        "create",
        "--type",
        "composer:placement",
        "--subject",
        "effort-p-missing",
        "--payload",
        json.dumps({}),
    )
    assert missing.returncode != 0
    assert "area" in _output(missing).lower()
    unknown = _run_canon(
        root,
        env,
        "create",
        "--type",
        "composer:placement",
        "--subject",
        "effort-p-unknown",
        "--payload",
        json.dumps({"area": "area-missing"}),
    )
    assert unknown.returncode != 0
    assert "area" in _output(unknown).lower()


def test_idea_status_only(tmp_path: Path):
    root, env, _ = _init_store_with_composer(tmp_path)
    idea = _run_canon(
        root,
        env,
        "create",
        "--type",
        "composer:idea",
        "--subject",
        "idea-1",
        "--payload",
        json.dumps({"status": "open"}),
    )
    assert idea.returncode == 0, _output(idea)


def test_idea_bad_status(tmp_path: Path):
    root, env, _ = _init_store_with_composer(tmp_path)
    valid = _run_canon(
        root,
        env,
        "create",
        "--type",
        "composer:idea",
        "--subject",
        "idea-good-status",
        "--payload",
        json.dumps({"status": "open"}),
    )
    assert valid.returncode == 0, _output(valid)
    invalid = _run_canon(
        root,
        env,
        "create",
        "--type",
        "composer:idea",
        "--subject",
        "idea-bad-status",
        "--payload",
        json.dumps({"status": "paused"}),
    )
    assert invalid.returncode != 0
    assert "status" in _output(invalid).lower()


def test_idea_bad_area(tmp_path: Path):
    root, env, _ = _init_store_with_composer(tmp_path)
    area = _create_area(root, env, "area-a")
    assert area.returncode == 0, _output(area)
    valid = _run_canon(
        root,
        env,
        "create",
        "--type",
        "composer:idea",
        "--subject",
        "idea-area-good",
        "--payload",
        json.dumps({"status": "open", "area": "area-a"}),
    )
    assert valid.returncode == 0, _output(valid)
    invalid = _run_canon(
        root,
        env,
        "create",
        "--type",
        "composer:idea",
        "--subject",
        "idea-area-bad",
        "--payload",
        json.dumps({"status": "open", "area": "area-missing"}),
    )
    assert invalid.returncode != 0
    assert "area" in _output(invalid).lower()


def test_idea_bad_effort(tmp_path: Path):
    root, env, _ = _init_store_with_composer(tmp_path)
    effort = _create_effort(root, env, "effort-a")
    assert effort.returncode == 0, _output(effort)
    valid = _run_canon(
        root,
        env,
        "create",
        "--type",
        "composer:idea",
        "--subject",
        "idea-effort-good",
        "--payload",
        json.dumps({"status": "open", "effort": "effort-a"}),
    )
    assert valid.returncode == 0, _output(valid)
    invalid = _run_canon(
        root,
        env,
        "create",
        "--type",
        "composer:idea",
        "--subject",
        "idea-effort-bad",
        "--payload",
        json.dumps({"status": "open", "effort": "effort-missing"}),
    )
    assert invalid.returncode != 0
    assert "effort" in _output(invalid).lower()


def test_idea_bad_phase(tmp_path: Path):
    root, env, _ = _init_store_with_composer(tmp_path)
    effort = _create_effort(root, env, "effort-b")
    assert effort.returncode == 0, _output(effort)
    phase = _create_phase(root, env, "phase-a", effort="effort-b")
    assert phase.returncode == 0, _output(phase)
    valid = _run_canon(
        root,
        env,
        "create",
        "--type",
        "composer:idea",
        "--subject",
        "idea-phase-good",
        "--payload",
        json.dumps({"status": "open", "phase": "phase-a"}),
    )
    assert valid.returncode == 0, _output(valid)
    invalid = _run_canon(
        root,
        env,
        "create",
        "--type",
        "composer:idea",
        "--subject",
        "idea-phase-bad",
        "--payload",
        json.dumps({"status": "open", "phase": "phase-missing"}),
    )
    assert invalid.returncode != 0
    assert "phase" in _output(invalid).lower()


def test_idea_supersede(tmp_path: Path):
    root, env, _ = _init_store_with_composer(tmp_path)
    created = _run_canon(
        root,
        env,
        "create",
        "--type",
        "composer:idea",
        "--subject",
        "idea-supersede",
        "--payload",
        json.dumps({"status": "open"}),
    )
    assert created.returncode == 0, _output(created)
    updated = _run_canon(
        root,
        env,
        "supersede",
        "--type",
        "composer:idea",
        "--subject",
        "idea-supersede",
        "--set",
        "status=promoted",
    )
    assert updated.returncode == 0, _output(updated)
    result = json.loads(updated.stdout)
    assert result["record"]["subject"] == "idea-supersede"
    assert result["record"]["payload"]["status"] == "promoted"
    assert result["predecessor"]["payload"]["status"] == "open"


def test_init_with_composer_and_create(tmp_path: Path):
    root, env, _ = _init_store_with_composer(tmp_path)
    validated = _run_canon(root, env, "validate")
    assert validated.returncode == 0, _output(validated)
    assert json.loads(validated.stdout)["status"] == "valid"
    area = _create_area(root, env, "area-init")
    assert area.returncode == 0, _output(area)
    idea = _run_canon(
        root,
        env,
        "create",
        "--type",
        "composer:idea",
        "--subject",
        "idea-init",
        "--payload",
        json.dumps({"status": "open", "area": "area-init"}),
    )
    assert idea.returncode == 0, _output(idea)


def test_installed_prefix_entry_point(installed_prefix, tmp_path: Path):
    assert installed_prefix["error"] is None, installed_prefix["error"]
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import importlib.metadata as md, json\n"
                "eps = md.entry_points()\n"
                "group = eps.select(group='canon.schemas') if hasattr(eps, 'select') else eps.get('canon.schemas', [])\n"
                "print(json.dumps({ep.name: ep.value for ep in group}, sort_keys=True))\n"
            ),
        ],
        cwd=str(elsewhere),
        env=installed_prefix["env"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, _output(proc)
    mapping = json.loads(proc.stdout or "{}")
    assert mapping.get("composer") == "orchestra.composer.schemas"


def test_installed_prefix_ships_composer_json(installed_prefix, tmp_path: Path):
    assert installed_prefix["error"] is None, installed_prefix["error"]
    elsewhere = tmp_path / "outside-checkout"
    elsewhere.mkdir()
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from pathlib import Path\n"
                "import orchestra\n"
                "print(Path(orchestra.__file__).resolve().parent / 'composer' / 'schemas' / 'composer.json')\n"
            ),
        ],
        cwd=str(elsewhere),
        env=installed_prefix["env"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, _output(proc)
    composer_json = Path(proc.stdout.strip())
    assert str(composer_json).startswith(str(installed_prefix["prefix"]))
    assert composer_json.is_file()


def test_boundary_rejects_composer_importing_conductor(tmp_path: Path):
    composer = tmp_path / "orchestra" / "composer"
    composer.mkdir(parents=True)
    (composer / "leak.py").write_text("from orchestra.conductor import suite\n", encoding="utf-8")
    assert boundary_violations(tmp_path / "orchestra") == [
        "orchestra/composer/leak.py:1: composer imports orchestra.conductor",
    ]


def test_boundary_accepts_composer_importing_canon_and_score(tmp_path: Path):
    composer = tmp_path / "orchestra" / "composer"
    composer.mkdir(parents=True)
    (composer / "ok.py").write_text(
        "from orchestra.canon import store\nfrom orchestra.score import schemas\n",
        encoding="utf-8",
    )
    assert boundary_violations(tmp_path / "orchestra") == []
