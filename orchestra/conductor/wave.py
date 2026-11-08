"""Start the next wave of a phase: pick ready tasks, cut task branches and worktrees, mark them in progress."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from orchestra.canon import record_payload
from orchestra.canon.git_backend import run_git
from orchestra.canon.project import Project
from orchestra.canon.types import DerivedValues, Record
from orchestra.score.workflow_blockers import WorkflowBlockerError, phase_blockers

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


def _effort(phase_rec: Record, phase: str) -> str:
    effort = record_payload(phase_rec).get("effort")
    return effort if isinstance(effort, str) else phase


def _open_question(project: Project, effort: str, phase: str, scope: str) -> Record | None:
    for record in project.list("score:continuity-question"):
        payload = record_payload(record)
        if (
            record["subject"] == effort
            and payload.get("scope") == scope
            and payload.get("phase") == phase
            and payload.get("blocking") is True
            and record["lifecycle_state"] == "open"
        ):
            return record
    return None


def _block(project: Project, phase_rec: Record, phase: str, scope: str) -> Record:
    effort = _effort(phase_rec, phase)
    existing = _open_question(project, effort, phase, scope)
    if existing is not None:
        return existing
    return project.create(
        record_type="score:continuity-question",
        subject=effort,
        payload={"owner": "user", "blocking": True, "scope": scope, "phase": phase},
    )


def worktree_root(cwd: Path) -> Path:
    result = run_git(cwd, "rev-parse", "--show-toplevel", capture_output=True, text=True)
    if result.returncode != 0:
        raise WaveError(f"not a git worktree: {cwd}")
    return Path(result.stdout.strip())


def block(project: Project, phase: str, scope: str) -> Record:
    return _block(project, phase_record(project.records(), phase), phase, scope)


def start(project: Project, repo: Path, phase: str, workdir: Path | None = None) -> WaveStart:
    records = project.records()
    try:
        blockers = phase_blockers(records, phase)
    except WorkflowBlockerError as exc:
        raise WaveError(str(exc)) from exc
    if blockers:
        names = ", ".join(blocker.record["subject"] for blocker in blockers)
        raise WaveError(f"phase {phase!r} is blocked by human decision: {names}")
    derived = project.derived(records)
    phase_rec = phase_record(records, phase)
    wave, chosen = select_wave(records, derived, phase)
    executor = check_executors(chosen)
    landing = has_landing(phase_rec)
    items = phase_items(records, phase)
    prepared: list[tuple[Record, str, str]] = []
    for item in chosen:
        if landing:
            try:
                tree, branch = _prepare(repo, phase, item, closes_phase(item, items))
            except WaveError as exc:
                _block(project, phase_rec, phase, f"merge:{item['subject']}")
                started_names = ", ".join(i["subject"] for i, _, _ in prepared) or "none"
                raise WaveError(f"{exc}; prepared before the conflict: {started_names}") from exc
            prepared.append((item, str(tree), branch))
        else:
            prepared.append((item, str(workdir or repo), ""))
    started: list[StartedTask] = []
    for item, write_root, branch in prepared:
        project.update(
            item["id"],
            record_type="score:work-item",
            transition="in_progress",
            payload={"assignee": executor, "write_root": write_root},
        )
        started.append(StartedTask(item["subject"], item["id"], executor, write_root, branch))
    return WaveStart(phase, wave, tuple(started))


@dataclass(frozen=True)
class WaveEnd:
    phase: str
    merged: tuple[str, ...]
    skipped: tuple[tuple[str, str], ...]
    conflict: str
    question_id: str


def _acceptances(records: list[Record], task: str, phase: str) -> list[Record]:
    return [
        r
        for r in records
        if r["record_type"] == "score:acceptance"
        and r["lifecycle_state"] == "active"
        and record_payload(r).get("phase") == phase
        and (r["subject"] == task or r["subject"].startswith(task + "-"))
    ]


def _passes(records: list[Record], acceptance: Record, tip: str) -> bool:
    runs = [
        r
        for r in records
        if r["record_type"] == "tuner:check-run"
        and record_payload(r).get("criterion_id") == acceptance["id"]
        and record_payload(r).get("revision") == tip
    ]
    if not runs:
        return False
    latest = record_payload(max(runs, key=lambda r: (r["recorded_at"], r["id"])))
    return latest.get("result") == "pass"


def end(project: Project, repo: Path, phase: str) -> WaveEnd:
    records = project.records()
    items = phase_items(records, phase)
    phase_tree = repo / ".worktrees" / phase
    phase_branch = f"phase/{phase}"
    phase_rec = phase_record(records, phase)
    merged: list[str] = []
    skipped: list[tuple[str, str]] = []
    for item in sorted(items, key=lambda r: r["subject"]):
        task = item["subject"]
        branch = f"task/{phase}/{task}"
        if closes_phase(item, items) or not _branch_exists(repo, branch):
            continue
        if item["lifecycle_state"] != "done":
            skipped.append((task, "task is not closed"))
            continue
        already = run_git(
            repo,
            "merge-base",
            "--is-ancestor",
            branch,
            phase_branch,
            capture_output=True,
            text=True,
        )
        if already.returncode == 0:
            continue
        acceptances = _acceptances(records, task, phase)
        tip = _git(repo, "rev-parse", branch)
        if not acceptances or not all(_passes(records, a, tip) for a in acceptances):
            skipped.append((task, "checks did not pass"))
            continue
        result = run_git(phase_tree, "merge", "--no-edit", branch, capture_output=True, text=True)
        if result.returncode != 0:
            unmerged = run_git(phase_tree, "ls-files", "--unmerged", capture_output=True, text=True)
            if not unmerged.stdout.strip():
                raise WaveError(
                    f"git merge {branch} failed: {result.stderr.strip() or result.stdout.strip()}"
                )
            question = _block(project, phase_rec, phase, f"merge:{task}")
            return WaveEnd(phase, tuple(merged), tuple(skipped), task, question["id"])
        merged.append(task)
    return WaveEnd(phase, tuple(merged), tuple(skipped), "", "")
