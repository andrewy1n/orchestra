"""Start the next wave of a phase: pick ready tasks, cut task branches and worktrees, mark them in progress."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from orchestra.canon import record_payload
from orchestra.canon.git_backend import run_git
from orchestra.canon.project import Project
from orchestra.canon.types import DerivedValues, Record

EXECUTORS = ("inline", "subagent")
_LIVE = ("planned", "in_progress", "done")


class WaveError(RuntimeError):
    """The wave cannot start; the message names what to fix."""


@dataclass(frozen=True)
class StartedTask:
    task: str
    id: str
    executor: str
    write_root: str
    branch: str


@dataclass(frozen=True)
class WaveStart:
    phase: str
    wave: int | None
    tasks: tuple[StartedTask, ...]


def repo_root(cwd: Path) -> Path:
    result = run_git(
        cwd,
        "rev-parse",
        "--path-format=absolute",
        "--git-common-dir",
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise WaveError(f"not a git repository: {cwd}")
    return Path(result.stdout.strip()).parent


def _git(cwd: Path, *args: str) -> str:
    result = run_git(cwd, *args, capture_output=True, text=True)
    if result.returncode != 0:
        raise WaveError(
            f"git {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout.strip()


def _branch_exists(repo: Path, branch: str) -> bool:
    return (
        run_git(
            repo,
            "rev-parse",
            "--verify",
            "--quiet",
            f"refs/heads/{branch}",
            capture_output=True,
            text=True,
        ).returncode
        == 0
    )


def has_landing(phase_record: Record) -> bool:
    return any(line.strip() == "## Landing" for line in phase_record.get("body", "").splitlines())


def phase_record(records: list[Record], phase: str) -> Record:
    found = [r for r in records if r["record_type"] == "score:phase" and r["subject"] == phase]
    if not found:
        raise WaveError(f"phase {phase!r} not found")
    return max(found, key=lambda r: r["recorded_at"])


def phase_items(records: list[Record], phase: str) -> list[Record]:
    return [
        r
        for r in records
        if r["record_type"] == "score:work-item"
        and r["lifecycle_state"] in _LIVE
        and record_payload(r).get("phase") == phase
    ]


def _depends_on(item: Record) -> list[str]:
    value = record_payload(item).get("depends_on")
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def closes_phase(item: Record, items: list[Record]) -> bool:
    others = [o for o in items if o["id"] != item["id"]]
    deps = _depends_on(item)
    return bool(others) and all(o["subject"] in deps or o["id"] in deps for o in others)


def _executor(item: Record) -> str:
    value = record_payload(item).get("executor")
    return value if isinstance(value, str) and value else "subagent"


def select_wave(
    records: list[Record], derived: dict[str, DerivedValues], phase: str
) -> tuple[int | None, list[Record]]:
    ready = [
        item
        for item in phase_items(records, phase)
        if item["lifecycle_state"] == "planned" and derived.get(item["id"], {}).get("ready")
    ]
    if not ready:
        raise WaveError(f"no ready work-item in phase {phase!r}")
    waves = [derived.get(item["id"], {}).get("wave") for item in ready]
    lowest = min((w for w in waves if w is not None), default=None)
    chosen = [i for i, w in zip(ready, waves, strict=True) if w == lowest]
    return lowest, sorted(chosen, key=lambda r: r["subject"])


def check_executors(items: list[Record]) -> str:
    bad = [i["subject"] for i in items if _executor(i) not in EXECUTORS]
    if bad:
        raise WaveError(f"unknown executor on: {', '.join(bad)}")
    modes = {_executor(i) for i in items}
    if len(modes) > 1:
        detail = ", ".join(f"{i['subject']}={_executor(i)}" for i in items)
        raise WaveError(f"tasks disagree on executor: {detail}")
    return modes.pop()


def _prepare(repo: Path, phase: str, item: Record, closing: bool) -> tuple[Path, str]:
    phase_branch = f"phase/{phase}"
    phase_tree = repo / ".worktrees" / phase
    if closing:
        return phase_tree, phase_branch
    branch = f"task/{phase}/{item['subject']}"
    tree = repo / ".worktrees" / f"{phase}--{item['subject']}"
    if not _branch_exists(repo, branch):
        _git(repo, "branch", branch, phase_branch)
    if not tree.exists():
        _git(repo, "worktree", "add", str(tree), branch)
    contains = run_git(
        tree, "merge-base", "--is-ancestor", phase_branch, "HEAD", capture_output=True, text=True
    )
    if contains.returncode != 0:
        merged = run_git(tree, "merge", "--no-edit", phase_branch, capture_output=True, text=True)
        if merged.returncode != 0:
            raise WaveError(f"merging {phase_branch} into {branch} conflicts; resolve it in {tree}")
    return tree, branch


def start(project: Project, repo: Path, phase: str) -> WaveStart:
    records = project.records()
    derived = project.derived(records)
    phase_rec = phase_record(records, phase)
    wave, chosen = select_wave(records, derived, phase)
    executor = check_executors(chosen)
    landing = has_landing(phase_rec)
    items = phase_items(records, phase)
    started: list[StartedTask] = []
    for item in chosen:
        if landing:
            tree, branch = _prepare(repo, phase, item, closes_phase(item, items))
            write_root = str(tree)
        else:
            write_root, branch = str(repo), ""
        project.update(
            item["id"],
            record_type="score:work-item",
            transition="in_progress",
            payload={"assignee": executor, "write_root": write_root},
        )
        started.append(StartedTask(item["subject"], item["id"], executor, write_root, branch))
    return WaveStart(phase, wave, tuple(started))
