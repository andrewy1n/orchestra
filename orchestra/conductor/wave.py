"""Start the next wave of a phase: pick ready tasks, cut task branches and worktrees, mark them in progress."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from orchestra.canon import record_payload
from orchestra.canon.project import Project
from orchestra.canon.project_config import (
    CONFIG_PATH,
    DEFAULT_SMALL_WAVE_BUDGET_MINUTES,
    ProjectConfigError,
    load_project_config,
)
from orchestra.canon.types import DerivedValues, Record
from orchestra.conductor.check import run_check
from orchestra.conductor.execution_cost import new_dispatch_markers
from orchestra.conductor.head_evidence import EvidenceIndex, acceptance_latest
from orchestra.score.executor import ExecutorTask, ExecutorWaveError, wave_executor
from orchestra.score.lookups import (
    acceptances_of,
    closing_work_item,
    current_phase,
    live_work_items,
)
from orchestra.score.requirements import acceptance_requirement_ids
from orchestra.score.workflow_blockers import WorkflowBlockerError, phase_blockers
from orchestra.tools import Git, ToolError


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
    execution_mode: str = "agent"
    runner: RunnerOutcome | None = None


@dataclass(frozen=True)
class RunnerOutcome:
    task: str
    state: str
    report_id: str
    checks: tuple[Mapping[str, object], ...]
    refusal_reasons: tuple[str, ...]
    code: int


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
    record = current_phase(phase, records)
    if record is None:
        raise WaveError(f"phase {phase!r} not found")
    return record


def phase_items(records: list[Record], phase: str) -> list[Record]:
    return live_work_items(phase, records)


def closing_task(records: list[Record], phase: str) -> Record | None:
    closing = closing_work_item(phase, records)
    if closing is not None:
        return closing
    items = phase_items(records, phase)
    if len(items) == 1 and record_payload(items[0]).get("assignee") == "runner":
        return items[0]
    return None


def is_closing_task(records: list[Record], phase: str, item: Record) -> bool:
    closing = closing_task(records, phase)
    return closing is not None and closing["id"] == item["id"]


def _execution_report(records: list[Record], task: str) -> Record | None:
    reports = [
        record
        for record in records
        if record["record_type"] == "conductor:execution-report"
        and record_payload(record).get("work_item") == task
    ]
    return (
        max(reports, key=lambda record: (record["recorded_at"], record["id"])) if reports else None
    )


def _integrated(repo: Path, phase: str, item: Record, records: list[Record]) -> bool:
    phase_branch = f"phase/{phase}"
    branch = f"task/{phase}/{item['subject']}"
    git = Git(repo)
    phase_head = git.resolve(phase_branch)
    if phase_head is None:
        raise WaveError(f"phase branch {phase_branch!r} could not be read")
    if git.resolve(f"refs/heads/{branch}") is not None:
        return git.is_ancestor(branch, phase_head)
    report = _execution_report(records, item["subject"])
    revision = record_payload(report).get("revision") if report is not None else None
    if not isinstance(revision, str) or not revision:
        raise WaveError(f"completed dependency {item['subject']!r} has no execution revision")
    if git.resolve(revision) is None:
        raise WaveError(f"execution revision for {item['subject']!r} could not be read")
    return git.is_ancestor(revision, phase_head)


def _runner_start(
    project: Project, repo: Path, phase: str, item: Record, items: list[Record]
) -> RunnerOutcome:
    from orchestra.conductor import land_task, task_close, verification

    others = [other for other in items if other["id"] != item["id"]]
    incomplete = [other["subject"] for other in others if other["lifecycle_state"] != "done"]
    if incomplete:
        return RunnerOutcome(
            item["subject"],
            item["lifecycle_state"],
            "",
            (),
            (f"dependencies are not done: {', '.join(incomplete)}",),
            1,
        )
    for other in others:
        try:
            integrated = _integrated(repo, phase, other, project.records())
        except (ToolError, WaveError) as exc:
            return RunnerOutcome(item["subject"], item["lifecycle_state"], "", (), (str(exc),), 1)
        if not integrated:
            return RunnerOutcome(
                item["subject"],
                item["lifecycle_state"],
                "",
                (),
                (f"dependency {other['subject']!r} is not integrated into the phase branch",),
                1,
            )
    if item["lifecycle_state"] == "planned":
        project.update(
            item["id"],
            record_type="score:work-item",
            transition="in_progress",
            payload={"assignee": "runner", "write_root": str(repo / ".worktrees" / phase)},
        )
    tree = repo / ".worktrees" / phase
    try:
        revision = Git(tree).head()
    except ToolError as exc:
        raise _wave_error(exc) from exc
    report = project.create(
        record_type="conductor:execution-report",
        subject=item["subject"],
        payload={
            "work_item": item["subject"],
            "result": "pass",
            "verdict": "pass",
            "revision": revision,
        },
        body=(
            f"subject: {item['subject']}\nrevision: {revision}\nkind: deliver\n"
            "result: pass\nverdict: pass\nevidence: runner closing checks"
        ),
    )
    landed = land_task.LandedTask(
        item["subject"], phase, "", revision, report["id"], (), "pass", "pass"
    )
    run = verification.run_closing_checks(project, landed)
    verified = set(run.verified)
    requirements = record_payload(item).get("requirements")
    required = (
        [value for value in requirements if isinstance(value, str)]
        if isinstance(requirements, list)
        else []
    )
    acceptances = land_task.acceptances_for(project, item["subject"], phase)
    outcomes = {check.acceptance_id: check.exit_code for check in run.checks}
    for requirement in required:
        related = [
            acceptance
            for acceptance in acceptances
            if requirement in acceptance_requirement_ids(acceptance)
        ]
        if related and all(outcomes.get(acceptance["id"]) == 0 for acceptance in related):
            verified.add(requirement)
    closure = task_close.close(project, landed, frozenset(verified), verification=run)
    checks = tuple(
        {
            "subject": check.subject,
            "result": (
                "pass" if check.exit_code == 0 else "pending" if check.exit_code == 3 else "fail"
            ),
            "exit_code": check.exit_code,
            "message": check.message,
        }
        for check in run.checks
    )
    return RunnerOutcome(
        item["subject"],
        closure.state,
        report["id"],
        checks,
        closure.reasons,
        closure.code,
    )


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


def check_executors(
    items: list[Record], small_wave_budget_minutes: int = DEFAULT_SMALL_WAVE_BUDGET_MINUTES
) -> str:
    tasks = [
        ExecutorTask(
            subject=item["subject"],
            size=_optional_string(record_payload(item).get("size")),
            estimate_minutes=_optional_integer(record_payload(item).get("estimate_minutes")),
            executor=_optional_string(record_payload(item).get("executor")),
            assignee=_optional_string(record_payload(item).get("assignee")),
        )
        for item in items
    ]
    try:
        return wave_executor(tasks, small_wave_budget_minutes=small_wave_budget_minutes)
    except ExecutorWaveError as exc:
        raise WaveError(str(exc)) from exc


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _optional_integer(value: object) -> int | None:
    return value if type(value) is int else None


def _small_wave_budget(project: Project) -> int:
    config_path = project.project_root / CONFIG_PATH
    if not config_path.exists() and not config_path.is_symlink():
        return DEFAULT_SMALL_WAVE_BUDGET_MINUTES
    try:
        return load_project_config(project.project_root).small_wave_budget_minutes
    except ProjectConfigError as exc:
        raise WaveError(str(exc)) from exc


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
    landing = has_landing(phase_rec)
    items = phase_items(records, phase)
    closer = closing_task(records, phase) if landing else None
    if closer is not None and all(
        item["lifecycle_state"] == "done" for item in items if item["id"] != closer["id"]
    ):
        outcome = _runner_start(project, repo, phase, closer, items)
        return WaveStart(phase, None, (), "runner", outcome)
    wave, chosen = select_wave(records, derived, phase)
    executor = check_executors(chosen, _small_wave_budget(project))
    prepared: list[tuple[Record, str, str]] = []
    for item in chosen:
        if landing:
            try:
                tree, branch = _prepare(repo, phase, item, is_closing_task(records, phase, item))
            except WaveError as exc:
                _block(project, phase_rec, phase, f"merge:{item['subject']}")
                started_names = ", ".join(i["subject"] for i, _, _ in prepared) or "none"
                raise WaveError(f"{exc}; prepared before the conflict: {started_names}") from exc
            prepared.append((item, str(tree), branch))
        else:
            prepared.append((item, str(workdir or repo), ""))
    started: list[StartedTask] = []
    for item, write_root, branch in prepared:
        markers = new_dispatch_markers()
        project.update(
            item["id"],
            record_type="score:work-item",
            transition="in_progress",
            payload={
                "assignee": executor,
                "write_root": write_root,
                "dispatch_id": markers.dispatch_id,
                "dispatch_started_at": markers.dispatch_started_at,
            },
        )
        started.append(StartedTask(item["subject"], item["id"], executor, write_root, branch))
    return WaveStart(phase, wave, tuple(started), "agent")


@dataclass(frozen=True)
class WaveEnd:
    phase: str
    merged: tuple[str, ...]
    skipped: tuple[tuple[str, str], ...]
    conflict: str
    question_id: str


def task_acceptances(records: list[Record], task: str, phase: str) -> list[Record]:
    item = next((i for i in live_work_items(phase, records) if i["subject"] == task), None)
    if item is None:
        return []
    return acceptances_of(phase, item, records, records)


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
        if is_closing_task(records, phase, item) or not _branch_exists(repo, branch):
            continue
        if item["lifecycle_state"] != "done":
            skipped.append((task, "task is not closed"))
            continue
        if Git(repo).run("merge-base", "--is-ancestor", branch, phase_branch).returncode == 0:
            continue
        acceptances = task_acceptances(records, task, phase)
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


def _merged_tasks(repo: Path, records: list[Record], phase: str, task: str) -> list[str]:
    merged: list[str] = []
    for item in phase_items(records, phase):
        slug = item["subject"]
        branch = f"task/{phase}/{slug}"
        if (
            slug == task
            or is_closing_task(records, phase, item)
            or not _branch_exists(repo, branch)
        ):
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
        tasks = [task, *_merged_tasks(repo, project.records(), phase, task)]
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
