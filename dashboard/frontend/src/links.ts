/**
 * Resolve known reference tokens to overlay / milestone hash links.
 */

import { phaseHref, recordHref, requirementHref, taskHref } from "./detail";
import type { EffortView, Snapshot } from "./types";

export type RefKind = "task" | "phase" | "requirement" | "record" | "milestone";

export interface ResolvedRef {
	kind: RefKind;
	href: string;
	label: string;
	/** Raw token (for title attribute). */
	token: string;
}

export interface RefContext {
	snapshot: Snapshot;
	/** Selected / ambient effort subject. */
	effort?: string | null;
	/** Ambient phase subject (for requirement resolution). */
	phase?: string | null;
	/** Optional detail payload fields that may carry titles. */
	detail?: {
		title?: string;
		subject?: string;
		record_type?: string;
		id?: string;
	} | null;
}

const REC_RE =
	/^rec-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const REQ_RE = /^R\d+$/;

function effortView(ctx: RefContext, name?: string | null): EffortView | null {
	const key = name || ctx.effort;
	if (!key) return null;
	return ctx.snapshot.efforts.find((row) => row.effort === key) ?? null;
}

function labelFor(title: string | undefined, token: string): string {
	const clean = (title || "").trim();
	if (clean) return clean;
	return token;
}

/**
 * Resolve a single standalone token against snapshot/detail context.
 * Returns null when the token is not a known shape or cannot be resolved.
 */
export function resolveRef(token: string, ctx: RefContext): ResolvedRef | null {
	const raw = (token || "").trim();
	if (!raw) return null;

	if (REC_RE.test(raw)) {
		const detailHit = ctx.detail?.id === raw ? ctx.detail : null;
		const title =
			detailHit?.title ||
			detailHit?.subject ||
			(detailHit?.record_type
				? `${detailHit.record_type} ${raw.slice(0, 12)}…`
				: undefined);
		return {
			kind: "record",
			href: recordHref(raw),
			label: labelFor(title, raw),
			token: raw,
		};
	}

	if (REQ_RE.test(raw)) {
		const effort = ctx.effort;
		const phase = ctx.phase;
		if (!effort || !phase) return null;
		return {
			kind: "requirement",
			href: requirementHref(effort, phase, raw),
			label: labelFor(`Requirement ${raw}`, raw),
			token: raw,
		};
	}

	const view = effortView(ctx);
	if (view) {
		const task = view.tasks.find(
			(row) => row.id === raw || row.subject === raw,
		);
		if (task) {
			return {
				kind: "task",
				href: taskHref(task.id),
				label: labelFor(task.title || task.subject, raw),
				token: raw,
			};
		}

		const phase = view.phases.find(
			(row) => row.subject === raw || row.title === raw,
		);
		if (phase) {
			return {
				kind: "phase",
				href: phaseHref(view.effort, phase.subject),
				label: labelFor(phase.title || phase.subject, raw),
				token: raw,
			};
		}

		const milestone = (view.milestones ?? []).find(
			(row) => row.subject === raw || row.title === raw,
		);
		if (milestone) {
			return {
				kind: "milestone",
				href: `#/milestone/${encodeURIComponent(view.effort)}/${encodeURIComponent(milestone.subject)}`,
				label: labelFor(milestone.title || milestone.subject, raw),
				token: raw,
			};
		}
	}

	// Cross-effort phase form: effort/phase
	const slash = raw.indexOf("/");
	if (slash > 0) {
		const effortName = raw.slice(0, slash);
		const phaseName = raw.slice(slash + 1);
		const other = effortView(ctx, effortName);
		const phase = other?.phases.find((row) => row.subject === phaseName);
		if (other && phase) {
			return {
				kind: "phase",
				href: phaseHref(other.effort, phase.subject),
				label: labelFor(phase.title || phase.subject, raw),
				token: raw,
			};
		}
	}

	return null;
}

/** Tokens that may appear as standalone words in prose / meta. */
const TOKEN_RE =
	/\b(rec-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|R\d+|[A-Za-z0-9][\w.-]*(?:\/[A-Za-z0-9][\w.-]*)?)\b/gi;

/**
 * Walk text and wrap resolved tokens in anchors. Unresolved text is escaped
 * by the caller when embedding; this returns HTML fragments with escaped
 * non-link spans when `escape` is true.
 */
export function linkifyText(
	text: string,
	ctx: RefContext,
	escapeText: (s: string) => string = (s) => s,
): string {
	const src = text || "";
	let last = 0;
	let out = "";
	TOKEN_RE.lastIndex = 0;
	for (let match = TOKEN_RE.exec(src); match; match = TOKEN_RE.exec(src)) {
		const token = match[0];
		const idx = match.index;
		if (idx > last) out += escapeText(src.slice(last, idx));
		const resolved = resolveRef(token, ctx);
		if (resolved) {
			const title = escapeText(resolved.token);
			out += `<a href="${escapeText(resolved.href)}" data-ref="${escapeText(resolved.kind)}" title="${title}">${escapeText(resolved.label)}</a>`;
		} else {
			out += escapeText(token);
		}
		last = idx + token.length;
	}
	if (last < src.length) out += escapeText(src.slice(last));
	return out;
}
