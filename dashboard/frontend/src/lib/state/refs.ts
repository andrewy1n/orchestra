import { openHash, requirementHref, taskHref } from "../../detail";
import { linkifyText, type RefContext } from "../../links";
import { renderMarkdown } from "../../markdown";
import { polling } from "./polling.svelte";
import { navigation } from "./route.svelte";

function escHtml(value: string): string {
	return value
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;");
}

export function linkContext(
	effort: string | null,
	phase: string | null,
	detail: unknown,
): RefContext | null {
	const snapshot = polling.snapshot;
	if (!snapshot) return null;
	return {
		snapshot,
		effort,
		phase,
		detail:
			detail && typeof detail === "object"
				? (detail as Record<string, unknown>)
				: null,
	};
}

export function linkify(text: string, linkCtx: RefContext | null): string {
	if (!linkCtx) return escHtml(text);
	return linkifyText(text, linkCtx, escHtml);
}

export function md(body: string, linkCtx: RefContext | null): string {
	return renderMarkdown(body, linkCtx);
}

export function openRequirement(id: string) {
	const route = navigation.route;
	const effortName = route.parts[1] || polling.effort?.effort || "";
	const phaseName = route.parts[2] || "";
	if (!effortName || !phaseName || !id) return;
	openHash(requirementHref(effortName, phaseName, id));
}

export function openGraphTask(id: string) {
	if (!id) return;
	openHash(taskHref(id));
}
