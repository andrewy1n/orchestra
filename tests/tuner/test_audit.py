"""bin/aff audit reverts diff blocks, labels them, and plants mutants in noticed blocks."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
AFF = REPO / "bin" / "aff"

BASE_APP = (
    "def add(a, b):\n"
    "    return a - b\n"
    "\n"
    "\n"
    "LIMIT = 1\n"
    "\n"
    "\n"
    "def mid():\n"
    "    return 0\n"
)
HEAD_APP = (
    "def add(a, b):\n"
    "    return a + b\n"
    "\n"
    "\n"
    "LIMIT = 2\n"
    "\n"
    "\n"
    "def mid():\n"
    "    return 0\n"
    "\n"
    "\n"
    "def extra():\n"
    "    return 5\n"
)
BASE_TEST = "def test_noop():\n    assert True\n"
HEAD_TEST = (
    "from app import add, extra\n"
    "\n"
    "\n"
    "def test_add():\n"
    "    assert add(1, 2) == 3\n"
    "\n"
    "\n"
    "def test_extra():\n"
    "    assert extra() == 5\n"
)
SYNTH_TESTS = ["tests/test_app.py::test_add", "tests/test_app.py::test_extra"]
PYTEST_INI = "[pytest]\npythonpath = .\n"

RANGE_BASE = "b3159b6"
RANGE_TIP = "c14dedb"
RANGE_TESTS = [
    "tests/test_close_batch.py::test_red_first_escape_permits_tdd_done_without_red_and_forces_human",
    "tests/test_close_batch.py::test_red_first_order_accepts_equal_sha",
    "tests/test_close_batch.py::test_red_first_order_accepts_when_green_descends_from_red",
    "tests/test_close_batch.py::test_red_first_order_dirty_red_requires_nonempty_diff_sha256",
    "tests/test_close_batch.py::test_red_first_order_dirty_red_without_digest_refused",
    "tests/test_close_batch.py::test_red_first_order_refuses_non_ancestor_on_divergent_history",
    "tests/test_close_batch.py::test_red_first_order_refuses_when_green_is_ancestor_of_red",
    "tests/test_close_batch.py::test_red_first_other_methods_check_closes_without_red_check_run_id",
    "tests/test_close_batch.py::test_red_first_other_methods_manual_closes_without_red_check_run_id",
    "tests/test_close_batch.py::test_red_first_pass_only_cli_exits_2",
    "tests/test_close_batch.py::test_red_first_pass_only_refuses_and_names_criterion",
    "tests/test_close_batch.py::test_red_first_request_accepts_fail_then_pass_with_dirty_red",
    "tests/test_close_batch.py::test_red_first_request_does_not_query_store",
    "tests/test_close_batch.py::test_red_first_request_refuses_non_runner_red",
    "tests/test_close_batch.py::test_red_first_request_refuses_red_result_not_fail",
    "tests/test_skill_contract_consistency.py::test_skill_invocations_are_permitted_by_contract[analyze-sessions/SKILL.md]",
    "tests/test_skill_contract_consistency.py::test_skill_invocations_are_permitted_by_contract[analyze-sessions/targets.md]",
    "tests/test_skill_contract_consistency.py::test_skill_invocations_are_permitted_by_contract[discuss/SKILL.md]",
    "tests/test_skill_contract_consistency.py::test_skill_invocations_are_permitted_by_contract[engage/SKILL.md]",
    "tests/test_skill_contract_consistency.py::test_skill_invocations_are_permitted_by_contract[ensure-store.md]",
    "tests/test_skill_contract_consistency.py::test_skill_invocations_are_permitted_by_contract[execute-phase/SKILL.md]",
    "tests/test_skill_contract_consistency.py::test_skill_invocations_are_permitted_by_contract[init/SKILL.md]",
    "tests/test_skill_contract_consistency.py::test_skill_invocations_are_permitted_by_contract[kinds-and-focus.md]",
    "tests/test_skill_contract_consistency.py::test_skill_invocations_are_permitted_by_contract[plan-phase/SKILL.md]",
    "tests/test_skill_contract_consistency.py::test_skill_invocations_are_permitted_by_contract[verify-work/SKILL.md]",
    "tests/test_assess_routing.py::test_verify_and_assess_are_separate_steps",
    "tests/test_assess_routing.py::test_routing_table_chooses_next_from_the_evidence",
    "tests/test_assess_routing.py::test_evidence_escalation_ladder",
    "tests/test_assess_routing.py::test_release_ready_only_when_every_requirement_is_verified",
    "tests/test_assess_routing.py::test_two_modes_skip_assessment_and_release",
    "tests/test_assess_routing.py::test_assessment_examples_carry_required_fields_and_sections",
    "tests/test_assess_routing.py::test_engage_routes_feedback_through_discuss",
    "tests/test_assess_routing.py::test_engage_documents_backlog_item_list_create_supersede",
    "tests/test_assess_routing.py::test_verify_work_documents_enforced_red_first_close",
    "tests/test_assess_routing.py::test_documented_invocations_are_contract_legal[verify-work]",
    "tests/test_assess_routing.py::test_documented_invocations_are_contract_legal[engage]",
    "tests/test_assess_routing.py::test_assessment_and_check_run_enums_match_the_contract",
]

CLOSE_BATCH = "scripts/close_batch.py"
DOCUMENTED_SURVIVORS = {
    "a-green-dirty-allowed",
    "a-tdd-revision-allowed",
    "a-missing-green-revision-ok",
}
KILLED_IDS = {"a-ancestor-swap", "a-ancestor-invert-rc", "a-red-result-inverted"}
LLM_MUTANTS = [
    {
        "id": "a-green-dirty-allowed",
        "file": CLOSE_BATCH,
        "patch": {
            "old": (
                '    if green_revision == "dirty":\n'
                "        raise CloseRefused(\n"
                '            f"criterion {criterion_id!r}: cannot verify red-first ordering "\n'
                '            "when green revision is dirty and red is a SHA"\n'
                "        )\n"
                "\n"
                "    if not _is_git_ancestor(red_revision, green_revision, cwd):"
            ),
            "new": "    if not _is_git_ancestor(red_revision, green_revision, cwd):",
        },
    },
    {
        "id": "a-tdd-revision-allowed",
        "file": CLOSE_BATCH,
        "patch": {
            "old": (
                '            if method == "check" and "revision" in entry:\n'
                "                raise CloseRequestError(\n"
                '                    f"criteria entry {criterion_id!r} method={method!r} must "\n'
                '                    "not carry revision/signed_by; reference check_run_id only"\n'
                "                )"
            ),
            "new": (
                '            if method == "check" and "signed_by" in entry:\n'
                "                raise CloseRequestError(\n"
                '                    f"criteria entry {criterion_id!r} method={method!r} must "\n'
                '                    "not carry revision/signed_by; reference check_run_id only"\n'
                "                )"
            ),
        },
    },
    {
        "id": "a-missing-green-revision-ok",
        "file": CLOSE_BATCH,
        "patch": {
            "old": (
                '    green_revision = entry.get("revision")\n'
                "    if not green_revision:\n"
                "        raise CloseRefused(\n"
                '            f"criterion {criterion_id!r}: green revision required for "\n'
                '            "git-ancestry red-first check"\n'
                "        )"
            ),
            "new": (
                '    green_revision = entry.get("revision")\n'
                "    if not green_revision:\n"
                "        return"
            ),
        },
    },
    {
        "id": "a-ancestor-swap",
        "file": CLOSE_BATCH,
        "patch": {
            "old": (
                '        ["git", "-C", str(cwd), "merge-base", "--is-ancestor", ancestor, descendant],'
            ),
            "new": (
                '        ["git", "-C", str(cwd), "merge-base", "--is-ancestor", descendant, ancestor],'
            ),
        },
    },
    {
        "id": "a-ancestor-invert-rc",
        "file": CLOSE_BATCH,
        "patch": {
            "old": "    return result.returncode == 0",
            "new": "    return result.returncode != 0",
        },
    },
    {
        "id": "a-red-result-inverted",
        "file": CLOSE_BATCH,
        "patch": {
            "old": '    if red_result != "fail":',
            "new": '    if red_result != "pass":',
        },
    },
]


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise AssertionError(f"git {args!r} failed\n{result.stderr}")
    return result.stdout


def _init(root: Path) -> None:
    root.mkdir(parents=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "test")
    _git(root, "config", "commit.gpgsign", "false")


def _write(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def _commit(root: Path, message: str) -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD").strip()


def _synthetic_repo(tmp_path: Path, extra_head: dict[str, str] | None = None):
    root = tmp_path / "repo"
    _init(root)
    _write(
        root,
        {
            "pytest.ini": PYTEST_INI,
            "app.py": BASE_APP,
            "tests/test_app.py": BASE_TEST,
            "README.md": "# app\n",
        },
    )
    base = _commit(root, "base")
    head_files = {
        "app.py": HEAD_APP,
        "tests/test_app.py": HEAD_TEST,
        "README.md": "# app\n\nNow with add and extra.\n",
    }
    head_files.update(extra_head or {})
    _write(root, head_files)
    head = _commit(root, "head")
    return root, base, head


def _audit(
    cwd: Path,
    base: str,
    head: str,
    tests: list[str] | None = None,
    mutants: Path | None = None,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    argv = [
        sys.executable,
        str(AFF),
        "audit",
        "--cwd",
        str(cwd),
        "--base",
        base,
        "--head",
        head,
    ]
    for node in tests or []:
        argv += ["--test", node]
    if mutants is not None:
        argv += ["--mutants", str(mutants)]
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)


def _payload(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.returncode == 0, proc.stderr or proc.stdout
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    assert len(lines) >= 1
    return json.loads(proc.stdout)


def _is_test_path(path: str) -> bool:
    parts = path.split("/")
    name = parts[-1]
    return (
        "tests" in parts[:-1]
        or "test" in parts[:-1]
        or (name.startswith("test_") and name.endswith(".py"))
        or name.endswith("_test.py")
        or name == "conftest.py"
    )


def _require_history() -> None:
    for sha in (RANGE_BASE, RANGE_TIP):
        probe = subprocess.run(
            ["git", "-C", str(REPO), "cat-file", "-e", f"{sha}^{{commit}}"],
            capture_output=True,
        )
        if probe.returncode != 0:
            pytest.skip(f"{sha} missing from repository history")


def test_r1_audit_labels_each_source_block(tmp_path: Path):
    """R1: audit splits the diff into blocks and labels each as noticed, not_noticed, or inconclusive."""
    root, base, head = _synthetic_repo(tmp_path)
    proc = _audit(root, base, head, tests=SYNTH_TESTS)
    payload = _payload(proc)
    assert payload["advisory"] is True
    assert payload["base"] == base
    assert payload["head"] == head
    assert isinstance(payload["mutants"], list)
    assert payload["survivors"] == []

    blocks = payload["blocks"]
    for block in blocks:
        assert {"file", "start", "end", "label", "text"} <= set(block)
        assert isinstance(block["start"], int) and isinstance(block["end"], int)
        assert block["end"] >= block["start"]
        assert block["label"] in {"noticed", "not_noticed", "inconclusive"}
    assert {b["file"] for b in blocks} == {"app.py"}

    by_text = {}
    for block in blocks:
        for key in ("return a + b", "LIMIT = 2", "def extra"):
            if key in block["text"]:
                by_text[key] = block
    assert set(by_text) == {"return a + b", "LIMIT = 2", "def extra"}
    assert by_text["return a + b"]["label"] == "noticed"
    assert by_text["return a + b"]["start"] == 2
    assert by_text["LIMIT = 2"]["label"] == "not_noticed"
    assert by_text["LIMIT = 2"]["start"] == 5
    assert by_text["def extra"]["label"] == "inconclusive"
    assert by_text["def extra"]["start"] >= 9
    assert len(blocks) == 3


def test_r1_audit_reads_claim_tests_from_manifest(tmp_path: Path):
    """R1: audit reruns tests of every claim in the head manifest through its runner."""
    root = tmp_path / "repo"
    _init(root)
    _write(
        root,
        {"pytest.ini": PYTEST_INI, "app.py": BASE_APP, "tests/test_app.py": BASE_TEST},
    )
    base = _commit(root, "base")
    manifest = {
        "claims": [
            {
                "id": "claim-add",
                "text": "add sums",
                "tests": ["tests/test_app.py::test_add"],
                "oracle_hashes": {},
            }
        ],
        "amendments": [],
    }
    _write(
        root,
        {
            "app.py": HEAD_APP,
            "tests/test_app.py": HEAD_TEST,
            ".affidavit/manifest.json": json.dumps(manifest, indent=2) + "\n",
        },
    )
    head = _commit(root, "head")
    payload = _payload(_audit(root, base, head))
    labels = {
        key: block["label"]
        for block in payload["blocks"]
        for key in ("return a + b", "LIMIT = 2")
        if key in block["text"]
    }
    assert labels == {"return a + b": "noticed", "LIMIT = 2": "not_noticed"}
    assert all(b["file"] == "app.py" for b in payload["blocks"])


def test_r2_audit_never_reports_test_file_blocks(tmp_path: Path):
    """R2: audit never reports a test-file or prose block as a finding target."""
    extra = {
        "tests/test_x.py": "def test_x():\n    assert 1 == 1\n",
        "pkg/test_y.py": "def test_y():\n    assert 2 == 2\n",
        "pkg/z_test.py": "def test_z():\n    assert 3 == 3\n",
        "test/helper.py": "VALUE = 1\n",
        "conftest.py": "VALUE = 2\n",
        "docs/notes.py": "NOTE = 'prose'\n",
        "NOTES.txt": "plain notes\n",
        ".artifacts/state.json": '{"x": 1}\n',
    }
    root, base, head = _synthetic_repo(tmp_path, extra_head=extra)
    proc = _audit(root, base, head, tests=SYNTH_TESTS)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    payload = json.loads(proc.stdout)
    files = [block["file"] for block in payload["blocks"]]
    assert files, "source block must still be reported"
    assert "app.py" in files
    for path in files:
        assert not _is_test_path(path), path
        assert not path.startswith(("docs/", ".artifacts/"))
        assert not path.endswith((".md", ".rst", ".txt"))
    assert set(files) == {"app.py"}


def test_r3_audit_reports_unnoticed_build_batch_cwd_block():
    """R3: on the red-first range the audit reports the unnoticed build_batch(request, cwd=args.cwd) block."""
    _require_history()
    proc = _audit(REPO, RANGE_BASE, RANGE_TIP, tests=RANGE_TESTS)
    payload = _payload(proc)
    blocks = payload["blocks"]
    target = [
        b
        for b in blocks
        if b["file"] == CLOSE_BATCH and "build_batch(request, cwd=args.cwd)" in b["text"]
    ]
    assert len(target) == 1
    assert target[0]["label"] == "not_noticed"
    assert target[0]["start"] == 326

    for block in blocks:
        assert not block["file"].startswith("tests/"), block["file"]
        assert not _is_test_path(block["file"]), block["file"]
        assert not block["file"].endswith(".md"), block["file"]
    close_batch = [b for b in blocks if b["file"] == CLOSE_BATCH]
    assert any(b["label"] == "noticed" for b in close_batch)
    assert any(b["label"] == "not_noticed" for b in close_batch)


def test_r4_audit_plants_mutants_only_in_noticed_blocks(tmp_path: Path):
    """R4: audit plants mutants only in noticed blocks and reports a documented surviving mutant."""
    _require_history()
    mutants_file = tmp_path / "mutants.json"
    mutants_file.write_text(json.dumps({"mutants": LLM_MUTANTS}))
    proc = _audit(
        REPO, RANGE_BASE, RANGE_TIP, tests=RANGE_TESTS, mutants=mutants_file
    )
    payload = _payload(proc)

    reported = {m["id"]: m for m in payload["mutants"]}
    assert {"id", "file", "status"} <= set(next(iter(reported.values())))
    assert set(reported) == {m["id"] for m in LLM_MUTANTS}
    assert {m["status"] for m in reported.values()} <= {
        "killed",
        "survived",
        "invalid",
        "skipped",
    }

    survivors = payload["survivors"]
    assert set(survivors) == {
        i for i, m in reported.items() if m["status"] == "survived"
    }
    assert set(survivors) & DOCUMENTED_SURVIVORS

    noticed_text = [
        b["text"]
        for b in payload["blocks"]
        if b["file"] == CLOSE_BATCH and b["label"] == "noticed"
    ]
    spec = {m["id"]: m for m in LLM_MUTANTS}
    for mutant_id, entry in reported.items():
        in_noticed = any(spec[mutant_id]["patch"]["old"] in t for t in noticed_text)
        if entry["status"] in {"killed", "survived"}:
            assert in_noticed, mutant_id
        if not in_noticed:
            assert entry["status"] == "skipped", mutant_id

    assert any(
        reported[i]["status"] == "killed" for i in KILLED_IDS if i in reported
    )
