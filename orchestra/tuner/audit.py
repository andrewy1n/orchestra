"""Advisory phase-end audit: label diff blocks and optionally plant mutants."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from affidavit.manifest import (
    DEFAULT_RUNNER,
    ManifestError,
    load_manifest,
    resolve_commit,
)
from affidavit.observation import maybe_record_observation
from affidavit.runner import run_tests

HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


@dataclass(frozen=True)
class _Hunk:
    file_path: str
    new_start: int
    new_count: int
    patch_text: str
    text: str


class AuditError(Exception):
    """Usage or git failure that should exit 2."""


PROBES_PATH = ".affidavit/probes.json"


def run_audit(
    cwd: Path | str,
    base: str,
    head: str,
    extra_tests: Sequence[str] = (),
    mutants_path: Path | str | None = None,
    max_mutants: int | None = 20,
    probes_path: Path | str | None = None,
) -> dict[str, Any]:
    """Label source hunks between ``base`` and ``head``; optionally plant mutants.

    Also runs declared probes from ``.affidavit/probes.json`` at head (or
    ``probes_path`` when given) and reports unclaimed differences. Returns
    an advisory JSON-shaped dict. Does not affect verdict.
    """
    root = Path(cwd)
    base_commit = resolve_commit(root, base)
    head_commit = resolve_commit(root, head)
    claim_tests, runner = _claim_tests_and_runner(root, head_commit, extra_tests)
    claim_ids = _claim_ids(root, head_commit)
    hunks = _source_hunks(root, base_commit, head_commit)
    probes = (
        _load_probes_file(Path(probes_path))
        if probes_path is not None
        else _load_probes(root, head_commit)
    )

    checked = _checkout(root, head_commit)
    if checked is None:
        raise AuditError(f"could not check out worktree at {head}")
    base_checked = _checkout(root, base_commit) if probes else None
    if probes and base_checked is None:
        _remove(root, checked)
        raise AuditError(f"could not check out worktree at {base}")
    try:
        worktree = checked[1]
        head_pass = _passing_tests(worktree, claim_tests, runner)
        blocks = [
            _label_block(worktree, hunk, head_pass, runner) for hunk in hunks
        ]
        mutants, survivors = _plant_mutants(
            worktree,
            blocks,
            head_pass,
            runner,
            mutants_path,
            max_mutants,
        )
        if base_checked is not None:
            _reset(worktree)
            _reset(base_checked[1])
            diffs = _probe_diffs(base_checked[1], worktree, probes, claim_ids)
        else:
            diffs = []
    finally:
        _remove(root, checked)
        _remove(root, base_checked)

    result = {
        "advisory": True,
        "base": base_commit,
        "head": head_commit,
        "blocks": blocks,
        "mutants": mutants,
        "survivors": survivors,
        "diffs": diffs,
    }
    _record_unbound(root, result, probes)
    return result


_TECHNIQUE_AUDIT = "audit"
_TECHNIQUE_PROBES = "probes"


def _record_unbound(
    root: Path,
    result: dict[str, Any],
    probes: Sequence[dict[str, Any]],
) -> None:
    """Record unbound audit and probe observations when a store is usable."""
    base = str(result["base"])
    head = str(result["head"])
    maybe_record_observation(
        root,
        technique=_TECHNIQUE_AUDIT,
        base_rev=base,
        head_rev=head,
        result="advisory",
        replay=_audit_replay(base, head),
        subject=_TECHNIQUE_AUDIT + ":" + base + ":" + head,
    )
    by_id = {str(probe.get("id", "")): probe for probe in probes}
    for diff in result["diffs"]:
        if not isinstance(diff, dict):
            continue
        probe_id = str(diff.get("probe") or "")
        if not probe_id:
            continue
        maybe_record_observation(
            root,
            technique=_TECHNIQUE_PROBES,
            base_rev=base,
            head_rev=head,
            result="diff",
            replay=_probe_replay(base, head, by_id.get(probe_id, {}), probe_id),
            subject=_TECHNIQUE_PROBES + ":" + probe_id + ":" + base + ":" + head,
        )


def _audit_replay(base: str, head: str) -> str:
    return json.dumps(
        {
            "technique": _TECHNIQUE_AUDIT,
            "base": base,
            "head": head,
            "argv": ["aff", "audit", "--base", base, "--head", head],
        },
        sort_keys=True,
    )


def _probe_replay(
    base: str, head: str, probe: dict[str, Any], probe_id: str
) -> str:
    hint: dict[str, Any] = {
        "technique": _TECHNIQUE_PROBES,
        "base": base,
        "head": head,
        "probe": probe_id,
        "argv": ["aff", "audit", "--base", base, "--head", head],
    }
    argv = probe.get("argv")
    if isinstance(argv, list):
        hint["probe_argv"] = argv
    target = probe.get("target")
    if target:
        hint["target"] = target
    args = probe.get("args")
    if isinstance(args, list):
        hint["args"] = args
    return json.dumps(hint, sort_keys=True)


def _claim_ids(root: Path, head_commit: str) -> set[str]:
    try:
        manifest = load_manifest(root, head_commit)
    except ManifestError:
        return set()
    return {claim.id for claim in manifest.claims}


def _load_probes(root: Path, head_commit: str) -> list[dict[str, Any]]:
    proc = subprocess.run(
        ["git", "-C", str(root), "show", f"{head_commit}:{PROBES_PATH}"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return []
    return _parse_probes(proc.stdout, PROBES_PATH)


def _load_probes_file(path: Path) -> list[dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AuditError(f"could not read probes file: {exc}") from exc
    return _parse_probes(text, str(path))


def _parse_probes(text: str, label: str) -> list[dict[str, Any]]:
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AuditError(f"invalid {label}: {exc}") from exc
    probes = raw.get("probes") if isinstance(raw, dict) else None
    if not isinstance(probes, list):
        raise AuditError(f"{label} must contain a probes list")
    return [p for p in probes if isinstance(p, dict)]


def _probe_diffs(
    base_wt: Path,
    head_wt: Path,
    probes: Sequence[dict[str, Any]],
    claim_ids: set[str],
) -> list[dict[str, Any]]:
    diffs: list[dict[str, Any]] = []
    for probe in probes:
        probe_id = str(probe.get("id", ""))
        cited = {str(c) for c in probe.get("claims", []) if c}
        if cited & claim_ids:
            continue
        base_out = _run_probe(base_wt, probe)
        head_out = _run_probe(head_wt, probe)
        if base_out == head_out:
            continue
        diffs.append(
            {
                "probe": probe_id,
                "base": base_out,
                "head": head_out,
            }
        )
    return diffs


def _run_probe(worktree: Path, probe: dict[str, Any]) -> dict[str, Any]:
    kind = str(probe.get("kind", "cli"))
    if kind == "cli":
        argv = probe.get("argv")
        if not isinstance(argv, list) or not all(isinstance(x, str) and x for x in argv):
            return {"exit_code": 2, "stdout": "", "stderr": "invalid argv"}
        proc = subprocess.run(
            argv,
            cwd=str(worktree),
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    if kind == "function":
        target = str(probe.get("target", ""))
        args = probe.get("args", [])
        if not target or not isinstance(args, list):
            return {"exit_code": 2, "stdout": "", "stderr": "invalid function probe"}
        script = (
            "import importlib, json, sys\n"
            f"mod_name, _, attr = {target!r}.partition(':')\n"
            "mod = importlib.import_module(mod_name)\n"
            "fn = getattr(mod, attr)\n"
            f"print(json.dumps(fn(*{args!r}), default=str))\n"
        )
        proc = subprocess.run(
            ["python3", "-c", script],
            cwd=str(worktree),
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    return {"exit_code": 2, "stdout": "", "stderr": f"unknown probe kind {kind!r}"}


def _claim_tests_and_runner(
    root: Path, head_commit: str, extra_tests: Sequence[str]
) -> tuple[list[str], tuple[str, ...]]:
    tests: list[str] = []
    runner: tuple[str, ...] = DEFAULT_RUNNER
    try:
        manifest = load_manifest(root, head_commit)
        runner = manifest.runner
        for claim in manifest.claims:
            for test_id in claim.tests:
                if test_id not in tests:
                    tests.append(test_id)
    except ManifestError:
        pass
    for test_id in extra_tests:
        if test_id not in tests:
            tests.append(test_id)
    return tests, runner


def _source_hunks(root: Path, base: str, head: str) -> list[_Hunk]:
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "diff",
            "-U0",
            base,
            head,
            "--",
            ".",
            ":(exclude).artifacts",
            ":(exclude).affidavit",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise AuditError(proc.stderr.strip() or "git diff failed")
    return [h for h in _parse_diff(proc.stdout) if _is_source_path(h.file_path)]


def _parse_diff(diff_text: str) -> list[_Hunk]:
    hunks: list[_Hunk] = []
    lines = diff_text.splitlines()
    i = 0
    current_file: str | None = None
    file_header: list[str] = []

    while i < len(lines):
        line = lines[i]
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                current_file = parts[3][2:] if parts[3].startswith("b/") else parts[3]
            else:
                current_file = None
            file_header = [line]
            i += 1
            while i < len(lines) and not lines[i].startswith("@@"):
                file_header.append(lines[i])
                i += 1
            continue
        if line.startswith("@@") and current_file:
            match = HUNK_HEADER.match(line)
            if not match:
                i += 1
                continue
            new_start = int(match.group(3))
            new_count = int(match.group(4) or "1")
            header = line
            body: list[str] = []
            i += 1
            while (
                i < len(lines)
                and not lines[i].startswith("diff --git ")
                and not lines[i].startswith("@@")
            ):
                body.append(lines[i])
                i += 1
            patch_lines = list(file_header)
            if not any(pl.startswith("--- ") for pl in patch_lines):
                patch_lines.extend([f"--- a/{current_file}", f"+++ b/{current_file}"])
            patch_lines.append(header)
            patch_lines.extend(body)
            added = [
                bl[1:] if bl.startswith("+") and not bl.startswith("+++") else ""
                for bl in body
                if bl.startswith("+") and not bl.startswith("+++")
            ]
            hunks.append(
                _Hunk(
                    file_path=current_file,
                    new_start=new_start,
                    new_count=new_count,
                    patch_text="\n".join(patch_lines) + "\n",
                    text="\n".join(added),
                )
            )
            continue
        i += 1
    return hunks


def _is_source_path(path: str) -> bool:
    if path.startswith(".artifacts/") or path == ".artifacts":
        return False
    if path.startswith(".affidavit/") or path == ".affidavit":
        return False
    if path.startswith("docs/") or "/docs/" in path:
        return False
    if path.endswith((".md", ".rst", ".txt")):
        return False
    parts = path.split("/")
    name = parts[-1]
    if "tests" in parts[:-1] or "test" in parts[:-1]:
        return False
    if name.startswith("test_") and name.endswith(".py"):
        return False
    if name.endswith("_test.py") or name == "conftest.py":
        return False
    return True


def _passing_tests(
    worktree: Path, tests: Sequence[str], runner: Sequence[str]
) -> list[str]:
    if not tests:
        return []
    outcomes = run_tests(worktree, tests, runner)
    return [t for t in tests if outcomes.get(t) == "passed"]


def _label_block(
    worktree: Path,
    hunk: _Hunk,
    head_pass: Sequence[str],
    runner: Sequence[str],
) -> dict[str, Any]:
    end = hunk.new_start if hunk.new_count == 0 else hunk.new_start + hunk.new_count - 1
    block = {
        "file": hunk.file_path,
        "start": hunk.new_start,
        "end": end,
        "label": "inconclusive",
        "text": hunk.text,
    }
    _reset(worktree)
    if not _reverse_apply(worktree, hunk.patch_text):
        return block
    if not head_pass:
        return block
    outcomes = run_tests(worktree, head_pass, runner)
    if any(outcomes.get(t) == "assertion_failed" for t in head_pass):
        block["label"] = "noticed"
    elif all(outcomes.get(t) == "passed" for t in head_pass):
        block["label"] = "not_noticed"
    return block


def _plant_mutants(
    worktree: Path,
    blocks: Sequence[dict[str, Any]],
    head_pass: Sequence[str],
    runner: Sequence[str],
    mutants_path: Path | str | None,
    max_mutants: int | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    if mutants_path is None:
        return [], []
    path = Path(mutants_path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"invalid mutants file: {exc}") from exc
    specs = raw.get("mutants") if isinstance(raw, dict) else None
    if not isinstance(specs, list):
        raise AuditError("mutants file must contain a mutants list")
    limit = 20 if max_mutants is None else max_mutants
    if limit >= 0:
        specs = specs[:limit]

    noticed_by_file: dict[str, list[str]] = {}
    for block in blocks:
        if block["label"] == "noticed":
            noticed_by_file.setdefault(block["file"], []).append(block["text"])

    reported: list[dict[str, Any]] = []
    survivors: list[str] = []
    for spec in specs:
        if not isinstance(spec, dict):
            continue
        mutant_id = str(spec.get("id", ""))
        file_path = str(spec.get("file", ""))
        patch = spec.get("patch") if isinstance(spec.get("patch"), dict) else {}
        old = str(patch.get("old", ""))
        new = str(patch.get("new", ""))
        entry: dict[str, Any] = {"id": mutant_id, "file": file_path, "status": "skipped"}
        in_noticed = any(old and old in text for text in noticed_by_file.get(file_path, ()))
        if not in_noticed or not old:
            reported.append(entry)
            continue
        _reset(worktree)
        target = worktree / file_path
        try:
            content = target.read_text(encoding="utf-8")
        except OSError:
            entry["status"] = "invalid"
            reported.append(entry)
            continue
        if old not in content:
            entry["status"] = "invalid"
            reported.append(entry)
            continue
        target.write_text(content.replace(old, new, 1), encoding="utf-8")
        if not head_pass:
            entry["status"] = "survived"
            survivors.append(mutant_id)
            reported.append(entry)
            continue
        outcomes = run_tests(worktree, head_pass, runner)
        if any(outcomes.get(t) == "assertion_failed" for t in head_pass):
            entry["status"] = "killed"
        elif all(outcomes.get(t) == "passed" for t in head_pass):
            entry["status"] = "survived"
            survivors.append(mutant_id)
        else:
            entry["status"] = "invalid"
        reported.append(entry)
    return reported, survivors


def _reset(worktree: Path) -> None:
    subprocess.run(
        ["git", "checkout", "--", "."],
        cwd=str(worktree),
        capture_output=True,
        check=False,
    )
    subprocess.run(
        ["git", "clean", "-fd"],
        cwd=str(worktree),
        capture_output=True,
        check=False,
    )


def _reverse_apply(worktree: Path, patch_text: str) -> bool:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".patch", delete=False) as handle:
        handle.write(patch_text)
        patch_path = handle.name
    try:
        proc = subprocess.run(
            ["git", "apply", "-R", "--unidiff-zero", patch_path],
            cwd=str(worktree),
            capture_output=True,
            text=True,
        )
        return proc.returncode == 0
    finally:
        Path(patch_path).unlink(missing_ok=True)


def _checkout(cwd: Path, commit: str) -> tuple[Path, Path] | None:
    parent = Path(tempfile.mkdtemp(prefix="aff-audit-"))
    worktree = parent / "wt"
    added = subprocess.run(
        ["git", "-C", str(cwd), "worktree", "add", "--detach", str(worktree), commit],
        capture_output=True,
    )
    if added.returncode != 0:
        shutil.rmtree(parent, ignore_errors=True)
        return None
    return parent, worktree


def _remove(cwd: Path, checked: tuple[Path, Path] | None) -> None:
    if checked is None:
        return
    parent, worktree = checked
    subprocess.run(
        ["git", "-C", str(cwd), "worktree", "remove", "--force", str(worktree)],
        capture_output=True,
    )
    shutil.rmtree(parent, ignore_errors=True)
