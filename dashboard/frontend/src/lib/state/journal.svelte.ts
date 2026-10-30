import { getJson } from "../../api";
import type { JournalResponse } from "../../api-types";
import { filterJournal, orderedJournal } from "../../side";
import { polling } from "./polling.svelte";
import { navigation } from "./route.svelte";

class JournalState {
	data = $state<JournalResponse | null>(null);
	error = $state("");
	filter = $state("");

	openCount = $derived(this.data ? this.data.open.length : null);

	effortName = $derived(
		navigation.route.name === "journal"
			? (navigation.route.parts[1] ?? "")
			: "",
	);

	items = $derived(filterJournal(orderedJournal(this.data), this.filter));

	reset() {
		this.data = null;
		this.error = "";
		this.filter = "";
	}
}

export const journal = new JournalState();

export function bindJournal() {
	journal.reset();

	$effect(() => {
		if (journal.effortName && journal.effortName !== polling.selectedEffort) {
			polling.selectedEffort = journal.effortName;
		}
	});

	$effect(() => {
		const name = journal.effortName || polling.effort?.effort || "";
		if (!name) {
			journal.data = null;
			journal.error = "";
			return;
		}
		let cancelled = false;
		journal.data = null;
		journal.error = "";
		void getJson<JournalResponse>(`journal?effort=${encodeURIComponent(name)}`)
			.then((data) => {
				if (!cancelled) {
					journal.data = data;
					journal.error = "";
				}
			})
			.catch((err: unknown) => {
				if (!cancelled) {
					journal.data = null;
					journal.error = err instanceof Error ? err.message : String(err);
				}
			});
		return () => {
			cancelled = true;
		};
	});
}
