import { leafTarget, openHash } from "../../detail";
import { currentRoute } from "../../router";
import { overlay } from "./overlay.svelte";
import { leaveHref } from "./polling.svelte";

export function handleKey(event: KeyboardEvent, toggleTheme: () => void) {
	if (event.key === "t" && !event.metaKey && !event.ctrlKey && !event.altKey) {
		const el = event.target;
		if (
			el instanceof HTMLElement &&
			el.closest("input, textarea, select, [contenteditable='true']")
		) {
			return;
		}
		if (overlay.pendingWrite || leafTarget(currentRoute())) return;
		event.preventDefault();
		toggleTheme();
		return;
	}
	if (event.key !== "Escape") return;
	if (overlay.pendingWrite) return;
	const current = currentRoute();
	if (leafTarget(current)) return;
	if (current.name === "journal") {
		openHash(leaveHref());
	}
}
