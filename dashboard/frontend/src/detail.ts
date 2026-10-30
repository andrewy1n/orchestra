/**
 * Detail overlays opened by hash routes.
 *
 * Each kind maps to a GET /api/… payload. Phase overlays also surface the
 * `tabs` list from `dashboard.model.tabs_for`.
 */

import { parseRoute, type Route, type RouteName } from "./router";

export type DetailKind =
	| "phase"
	| "task"
	| "requirement"
	| "record"
	| "needs"
	| "backlog";

const DETAIL_KINDS: ReadonlySet<string> = new Set<DetailKind>([
	"phase",
	"task",
	"requirement",
	"record",
	"needs",
	"backlog",
]);

export interface DetailTarget {
	kind: DetailKind;
	/** Path for `getJson`, e.g. `phase?effort=…&phase=…`. */
	apiPath: string;
	/** Selected phase tab when `kind` is `phase`. */
	tab?: string;
}

function enc(value: string): string {
	return encodeURIComponent(value);
}

/** True when the route names a detail overlay. */
export function isDetailRoute(route: Route): boolean {
	return DETAIL_KINDS.has(route.name);
}

/**
 * Resolve the API path (and optional phase tab) for a detail hash route.
 * Returns null when the route is home/picker or missing required parts.
 */
export function detailTarget(route: Route): DetailTarget | null {
	const kind = route.name as DetailKind;
	if (!DETAIL_KINDS.has(kind)) return null;
	const parts = route.parts;

	if (kind === "phase") {
		// #/phase/{effort}/{phase}[/tab/{tab}]
		const effort = parts[1];
		const phase = parts[2];
		if (!effort || !phase) return null;
		const tab = parts[3] === "tab" && parts[4] ? parts[4] : undefined;
		return {
			kind,
			apiPath: `phase?effort=${enc(effort)}&phase=${enc(phase)}`,
			tab,
		};
	}

	if (kind === "task") {
		// #/task/{id}
		const id = parts[1];
		if (!id) return null;
		return { kind, apiPath: `task?id=${enc(id)}` };
	}

	if (kind === "requirement") {
		// #/requirement/{effort}/{phase}/{id}
		const effort = parts[1];
		const phase = parts[2];
		const id = parts[3];
		if (!effort || !phase || !id) return null;
		return {
			kind,
			apiPath: `requirement?effort=${enc(effort)}&phase=${enc(phase)}&id=${enc(id)}`,
		};
	}

	if (kind === "record") {
		// #/record/{id}
		const id = parts[1];
		if (!id) return null;
		return { kind, apiPath: `record?id=${enc(id)}` };
	}

	if (kind === "needs") {
		// #/needs/{effort}/{id}
		const effort = parts[1];
		const id = parts[2];
		if (!effort || !id) return null;
		return {
			kind,
			apiPath: `needs?effort=${enc(effort)}&id=${enc(id)}`,
		};
	}

	if (kind === "backlog") {
		// #/backlog/{effort}/{id}
		const effort = parts[1];
		const id = parts[2];
		if (!effort || !id) return null;
		return {
			kind,
			apiPath: `backlog?effort=${enc(effort)}&id=${enc(id)}`,
		};
	}

	return null;
}

/** Hash href that opens a phase overlay (optional tab). */
export function phaseHref(effort: string, phase: string, tab?: string): string {
	const base = `#/phase/${enc(effort)}/${enc(phase)}`;
	return tab && tab !== "overview" ? `${base}/tab/${enc(tab)}` : base;
}

/** Hash href that opens a task overlay. */
export function taskHref(id: string): string {
	return `#/task/${enc(id)}`;
}

/** Hash href that opens a requirement overlay. */
export function requirementHref(
	effort: string,
	phase: string,
	id: string,
): string {
	return `#/requirement/${enc(effort)}/${enc(phase)}/${enc(id)}`;
}

/** Hash href that opens an area screen. */
export function areaHref(subject: string): string {
	return `#/area/${enc(subject)}`;
}

/** Hash href that opens the Home screen of an effort. */
export function effortHref(name: string): string {
	return `#/effort/${enc(name)}`;
}

/** Hash href that opens a journal record overlay. */
export function recordHref(id: string): string {
	return `#/record/${enc(id)}`;
}

/** Hash href that opens the journal screen for an effort. */
export function journalHref(effort: string): string {
	return `#/journal/${enc(effort)}`;
}

/** Hash href that opens a Needs you overlay. */
export function needsHref(effort: string, id: string): string {
	return `#/needs/${enc(effort)}/${enc(id)}`;
}

/** Hash href that opens a backlog overlay. */
export function backlogHref(effort: string, id: string): string {
	return `#/backlog/${enc(effort)}/${enc(id)}`;
}

/** Screens left behind by in-app navigation. Back pops this, not the dashboard. */
const backStack: string[] = [];
let rewinding = false;

function hashPath(hash: string): string {
	return hash.replace(/^#/, "");
}

/** Same phase with a different tab is one screen, not a back step. */
function sameScreen(current: string, next: string): boolean {
	const left = detailTarget(parseRoute(current));
	const right = detailTarget(parseRoute(next));
	return (
		!!left && !!right && left.kind === "phase" && left.apiPath === right.apiPath
	);
}

/** Navigate to a hash without leaving the SPA document. */
export function openHash(hash: string): void {
	if (typeof window === "undefined") return;
	const next = hashPath(hash);
	const current = hashPath(window.location.hash);
	if (current === next) {
		if (!next) backStack.length = 0;
		return;
	}
	if (!rewinding) {
		if (!next) backStack.length = 0;
		else if (current && !sameScreen(current, next)) backStack.push(current);
	}
	window.location.hash = next;
}

/**
 * Overlay Back / Esc. Step to the previous in-app screen.
 * With no in-app history, open `fallback`.
 */
export function closeDetail(fallback = ""): void {
	const prev = backStack.pop();
	rewinding = true;
	openHash(prev ?? fallback);
	rewinding = false;
}

export function isDetailKind(name: RouteName): name is DetailKind {
	return DETAIL_KINDS.has(name);
}
