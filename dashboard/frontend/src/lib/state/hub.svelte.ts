import { getJson } from "../../api";
import type { HubResponse } from "../../api-types";
import { polling } from "./polling.svelte";

class HubState {
	data = $state<HubResponse | null>(null);
	loaded = $state(false);
	error = $state("");

	reset() {
		this.data = null;
		this.loaded = false;
		this.error = "";
	}
}

export const hub = new HubState();

/** Reloads GET /api/hub whenever the snapshot token changes. */
export function bindHub() {
	hub.reset();

	$effect(() => {
		if (!polling.snapshot?.token) return;
		let cancelled = false;
		void getJson<HubResponse>("hub")
			.then((data) => {
				if (cancelled) return;
				hub.loaded = true;
				hub.data = data;
				hub.error = "";
			})
			.catch((err: unknown) => {
				if (cancelled) return;
				hub.loaded = true;
				hub.error = err instanceof Error ? err.message : String(err);
			});
		return () => {
			cancelled = true;
		};
	});
}
