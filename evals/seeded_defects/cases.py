from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from evals.seeded_defects.trees import PatchDoesNotApply, build_case_tree

KINDS = ("synthetic-defect", "real-escape", "control")
DEFECT_TYPES = ("reverted-change", "removed-test")
DEFECT_KINDS = ("synthetic-defect", "real-escape")


class CaseSetError(Exception):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("\n".join(errors))
        self.errors = errors


@dataclass(frozen=True)
class Case:
    id: str
    phase: str
    revision: str
    kind: str
    defect_type: str | None
    patch: Path | None
    expected_files: frozenset[str]
    expected_requirement_ids: frozenset[str]


def _strings(value: object) -> frozenset[str]:
    if not isinstance(value, list):
        return frozenset()
    return frozenset(str(item) for item in value)  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]


def _load_case(folder: Path, source_repo: Path, errors: list[str]) -> Case | None:
    case_id = folder.name
    start = len(errors)
    try:
        raw = json.loads((folder / "case.json").read_text())
    except (OSError, ValueError) as exc:
        errors.append(f"{case_id}: unreadable case.json: {exc}")
        return None
    if not isinstance(raw, dict):
        errors.append(f"{case_id}: case.json is not an object")
        return None
    meta: dict[str, object] = raw  # pyright: ignore[reportUnknownVariableType]
    phase = meta.get("phase")
    revision = meta.get("revision")
    kind = meta.get("kind")
    defect_type = meta.get("defect_type")
    if not isinstance(phase, str) or not phase:
        errors.append(f"{case_id}: missing phase")
    if not isinstance(revision, str) or not revision:
        errors.append(f"{case_id}: missing revision")
    if kind not in KINDS:
        errors.append(f"{case_id}: unknown kind {kind!r}")
    if kind == "synthetic-defect" and defect_type not in DEFECT_TYPES:
        errors.append(f"{case_id}: unknown defect type {defect_type!r}")
    expected_files = _strings(meta.get("expected_files"))
    expected_ids = _strings(meta.get("expected_requirement_ids"))
    patch_file = folder / "defect.patch"
    patch = patch_file if patch_file.is_file() else None
    if kind in DEFECT_KINDS:
        if patch is None:
            errors.append(f"{case_id}: defect case has no patch")
        if not expected_files and not expected_ids:
            errors.append(f"{case_id}: defect case has no expected catch")
    if not (folder / "records.json").is_file():
        errors.append(f"{case_id}: phase {phase!r} has no frozen records")
    if patch is not None and isinstance(revision, str) and revision and len(errors) == start:
        _check_patch(case_id, source_repo, revision, patch, errors)
    if len(errors) != start:
        return None
    return Case(
        id=case_id,
        phase=str(phase),
        revision=str(revision),
        kind=str(kind),
        defect_type=defect_type if isinstance(defect_type, str) else None,
        patch=patch,
        expected_files=expected_files,
        expected_requirement_ids=expected_ids,
    )


def _check_patch(
    case_id: str, source_repo: Path, revision: str, patch: Path, errors: list[str]
) -> None:
    with tempfile.TemporaryDirectory() as scratch:
        try:
            build_case_tree(source_repo, revision, patch, Path(scratch) / "tree")
        except PatchDoesNotApply as exc:
            errors.append(f"{case_id}: patch does not apply: {exc.stderr.strip()}")
        except (RuntimeError, subprocess.CalledProcessError) as exc:
            errors.append(f"{case_id}: cannot build tree at {revision}: {exc}")


def load_case_set(directory: Path, source_repo: Path) -> list[Case]:
    errors: list[str] = []
    cases: list[Case] = []
    folders = sorted(p for p in directory.iterdir() if p.is_dir()) if directory.is_dir() else []
    if not folders:
        errors.append(f"no cases found in {directory}")
    for folder in folders:
        case = _load_case(folder, source_repo, errors)
        if case is not None:
            cases.append(case)
    if errors:
        raise CaseSetError(errors)
    return cases
