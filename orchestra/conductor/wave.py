"""Start the next wave of a phase: pick ready tasks, cut task branches and worktrees, mark them in progress."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from orchestra.canon import record_payload
from orchestra.canon.project import Project
from orchestra.canon.types import DerivedValues, Record
from orchestra.conductor.check import run_check
from orchestra.conductor.head_evidence import EvidenceIndex, acceptance_latest
from orchestra.score.workflow_blockers import WorkflowBlockerError, phase_blockers
from orchestra.tools import Git, ToolError

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
    result = Git(cwd).run("rev-parse", "--path-format=absolute", "--git-common-dir")
    if result.returncode != 0:
        raise WaveError(f"not a git repository: {cwd}")
    return Path(result.stdout.strip()).parent


def _wave_error(error: ToolError) -> WaveError:
    detail = error.stderr.strip() or str(error)
    return WaveError(f"git {' '.join(error.argv[1:])} failed: {detail}")


def _git_text(cwd: Path, *args: str) -> str:
    try:
        return Git(cwd).text(*args)
    except ToolError as error:
        raise _wave_error(error) from error


def _branch_exists(repo: Path, branch: str) -> bool:
    return Git(repo).resolve(f"refs/heads/{branch}") is not None


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
        try:
            Git(repo).create_branch(branch, phase_branch)
        except ToolError as error:
            raise _wave_error(error) from error
    if not tree.exists():
        try:
            Git(repo).add_worktree(tree, branch)
        except ToolError as error:
            raise _wave_error(error) from error
    task_git = Git(tree)
    behind = task_git.run("merge-base", "--is-ancestor", phase_branch, "HEAD").returncode != 0
    if behind and not task_git.merge(phase_branch).clean:
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
    result = Git(cwd).run("rev-parse", "--show-toplevel")
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


def end(project: Project, repo: Path, phase: str) -> WaveEnd:
    records = project.records()
    index = EvidenceIndex(records)
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
        if Git(repo).run("merge-base", "--is-ancestor", branch, phase_branch).returncode == 0:
            continue
        acceptances = _acceptances(records, task, phase)
        tip = Git(repo).resolve(branch)
        if tip is None:
            raise WaveError(f"cannot resolve task branch {branch}")
        if not acceptances or not all(acceptance_latest(index, a, tip).holds for a in acceptances):
            skipped.append((task, "checks did not pass"))
            continue
        result = Git(phase_tree).merge(branch)
        if not result.clean:
            if not result.unmerged:
                raise WaveError(f"git merge {branch} failed: {result.output.strip()}")
            question = _block(project, phase_rec, phase, f"merge:{task}")
            return WaveEnd(phase, tuple(merged), tuple(skipped), task, question["id"])
        merged.append(task)
    return WaveEnd(phase, tuple(merged), tuple(skipped), "", "")


@dataclass(frozen=True)
class WaveResolve:
    phase: str
    task: str
    refusals: tuple[str, ...]
    commit: str = ""
    checks: tuple[tuple[str, int], ...] = ()

    @property
    def ready(self) -> bool:
        return not self.refusals


_CONFLICT_MARKER = re.compile(r"^(<<<<<<<|>>>>>>>)( |$)")


def _lines(output: str) -> list[str]:
    return [line for line in output.splitlines() if line]


def _marker_paths(tree: Path, paths: list[str]) -> list[str]:
    found: list[str] = []
    for path in paths:
        target = tree / path
        if not target.is_file():
            continue
        text = target.read_text(encoding="utf-8", errors="replace")
        if any(_CONFLICT_MARKER.match(line) for line in text.splitlines()):
            found.append(path)
    return found


def _guard_refusals(
    project: Project, phase_rec: Record, phase: str, task: str, tree: Path
) -> list[str]:
    refusals: list[str] = []
    scope = f"merge:{task}"
    if _open_question(project, _effort(phase_rec, phase), phase, scope) is None:
        refusals.append(f"no open {scope} question")
    unmerged = _lines(_git_text(tree, "diff", "--name-only", "--diff-filter=U"))
    if unmerged:
        refusals.append(
            "unmerged paths remain: " + ", ".join(unmerged) + " (edit them, then run git add)"
        )
    changed = _lines(_git_text(tree, "diff", "--name-only", "HEAD"))
    markers = _marker_paths(tree, sorted({*changed, *unmerged}))
    if markers:
        refusals.append("conflict marker remains in: " + ", ".join(markers))
    return refusals


def _merged_tasks(repo: Path, phase: str, items: list[Record], task: str) -> list[str]:
    merged: list[str] = []
    for item in items:
        slug = item["subject"]
        branch = f"task/{phase}/{slug}"
        if slug == task or closes_phase(item, items) or not _branch_exists(repo, branch):
            continue
        if Git(repo).is_ancestor(branch, f"phase/{phase}"):
            merged.append(slug)
    return merged


def resolve(project: Project, repo: Path, phase: str, task: str) -> WaveResolve:
    phase_rec = phase_record(project.records(), phase)
    tree = repo / ".worktrees" / phase
    from orchestra.conductor.land_task import acceptances_for

    refusals = _guard_refusals(project, phase_rec, phase, task, tree)
    if refusals:
        return WaveResolve(phase, task, tuple(refusals))
    _git_text(tree, "add", "-A", "--", ".", ":!.canon")
    branch = f"task/{phase}/{task}"
    merged_tree = _git_text(tree, "write-tree")
    commit = _git_text(
        tree,
        "commit-tree",
        merged_tree,
        "-p",
        "HEAD",
        "-p",
        branch,
        "-m",
        f"Merge branch '{branch}' into phase/{phase}",
    )
    trial = repo / ".worktrees" / f"{phase}--resolve-{task}"
    _git_text(repo, "worktree", "add", "--detach", "--force", str(trial), commit)
    failures: list[str] = []
    outcomes: list[tuple[str, int]] = []
    try:
        items = phase_items(project.records(), phase)
        tasks = [task, *_merged_tasks(repo, phase, items, task)]
        for slug in tasks:
            for acceptance in sorted(
                acceptances_for(project, slug, phase), key=lambda r: r["subject"]
            ):
                outcome = run_check(
                    acceptance_id=acceptance["id"],
                    cwd=trial,
                    store_root=project.project_root,
                    store_dir=project.store_path,
                )
                outcomes.append((acceptance["subject"], outcome.exit_code))
                if outcome.exit_code != 0:
                    failures.append(acceptance["subject"])
    finally:
        _git_text(repo, "worktree", "remove", "--force", str(trial))
    if failures:
        reason = "acceptance failed on the merge: " + ", ".join(failures)
        return WaveResolve(phase, task, (reason,), commit, tuple(outcomes))
    _git_text(tree, "merge", "--quit")
    _git_text(tree, "reset", "--soft", commit)
    question = _open_question(project, _effort(phase_rec, phase), phase, f"merge:{task}")
    if question is not None:
        project.update(
            question["id"], record_type="score:continuity-question", transition="answered"
        )
    return WaveResolve(phase, task, (), commit, tuple(outcomes))
