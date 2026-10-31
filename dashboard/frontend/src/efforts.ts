import type { TaskRow } from "./api-types";
import type { EffortView, StatusTab } from "./types";

/** Statuses included by each status tab (spike / TUI vocabulary). */
export const TAB_STATUSES: Record<StatusTab, readonly string[] | null> = {
	active: ["running", "ready", "waiting"],
	running: ["running"],
	ready: ["ready"],
	waiting: ["waiting"],
	done: ["done", "withdrawn"],
	all: null,
};

export const STATUS_TABS: ReadonlyArray<{ name: StatusTab; label: string }> = [
	{ name: "active", label: "Active" },
	{ name: "running", label: "Running" },
	{ name: "ready", label: "Ready" },
	{ name: "waiting", label: "Waiting" },
	{ name: "done", label: "Done" },
	{ name: "all", label: "All" },
];

export interface VisibleEfforts {
	shown: EffortView[];
	/** Finished efforts with no Needs you items that are currently hidden. */
	hidden: number;
}

/**
 * Rail visibility: live efforts, finished efforts that still need you, and
 * (optionally) finished efforts with nothing pending.
 */
export function visibleEfforts(
	efforts: EffortView[],
	showFinished: boolean,
): VisibleEfforts {
	const live = efforts.filter((view) => !view.finished);
	const finished = efforts.filter((view) => view.finished);
	const withNeeds = finished.filter((view) => view.needs_you.length > 0);
	const optional = finished.filter((view) => view.needs_you.length === 0);
	const shown = live.concat(withNeeds, showFinished ? optional : []);
	return { shown, hidden: showFinished ? 0 : optional.length };
}

/** Default phase: first in_progress, else first planned by ordinal, else null (all). */
export function defaultPhase(effort: EffortView): string | null {
	if (!effort.phases.length) return null;
	const inProgress = effort.phases.filter((p) => p.state === "in_progress");
	if (inProgress.length) return inProgress[0]!.subject;
	const planned = effort.phases
		.filter((p) => p.state === "planned")
		.slice()
		.sort((a, b) => a.ordinal - b.ordinal);
	if (planned.length) return planned[0]!.subject;
	return null;
}

/**
 * Resolve the phase filter. `pinned` is `"all"`, a phase subject, or `null`
 * (follow the default phase).
 */
export function resolvedPhase(
	effort: EffortView,
	pinned: string | null,
): string | null {
	if (pinned === "all") return null;
	if (pinned && effort.phases.some((p) => p.subject === pinned)) return pinned;
	return defaultPhase(effort);
}

/** Tasks limited to one phase, or every task when `phaseSubject` is null. */
export function scopedTasks(
	effort: EffortView,
	phaseSubject: string | null,
): TaskRow[] {
	return effort.tasks.filter(
		(task) => phaseSubject === null || task.phase === phaseSubject,
	);
}

/** Apply phase scope and a status tab. */
export function filteredTasks(
	effort: EffortView,
	phaseSubject: string | null,
	tab: StatusTab,
): TaskRow[] {
	const pool = scopedTasks(effort, phaseSubject);
	const allow = TAB_STATUSES[tab];
	return allow ? pool.filter((task) => allow.includes(task.status)) : pool;
}

/** Tab counts for the scoped phase. */
export function tabCounts(
	effort: EffortView,
	phaseSubject: string | null,
): Record<StatusTab, number> {
	const pool = scopedTasks(effort, phaseSubject);
	const out = {} as Record<StatusTab, number>;
	for (const { name } of STATUS_TABS) {
		const allow = TAB_STATUSES[name];
		out[name] = allow
			? pool.filter((task) => allow.includes(task.status)).length
			: pool.length;
	}
	return out;
}

const DEFAULT_TAB_ORDER: readonly StatusTab[] = [
	"active",
	"done",
	"waiting",
	"ready",
	"running",
	"all",
];

export function defaultStatusTab(counts: Record<StatusTab, number>): StatusTab {
	return DEFAULT_TAB_ORDER.find((name) => counts[name] > 0) ?? "all";
}
