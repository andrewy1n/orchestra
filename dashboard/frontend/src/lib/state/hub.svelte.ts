import { getJson } from "../../api";
import type { HubResponse } from "../../api-types";
import { polling } from "./polling.svelte";
import { navigation } from "./route.svelte";

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

function isHub(data: unknown): data is HubResponse {
	if (typeof data !== "object" || data === null) return false;
	const body = data as Record<string, unknown>;
	return (
		Array.isArray(body.work_next) &&
		Array.isArray(body.needs_you) &&
		Array.isArray(body.active_phases) &&
		Array.isArray(body.open_ideas)
	);
}

export function bindHub() {
	hub.reset();
	const active = $derived(navigation.route.name === "home");

	$effect(() => {
		polling.generation;
		if (!active) return;
		let cancelled = false;
		void getJson<HubResponse>("hub")
			.then((data) => {
				if (cancelled) return;
				hub.loaded = true;
				if (isHub(data)) {
					hub.data = data;
					hub.error = "";
				} else {
					hub.data = null;
					hub.error = "Hub response is not a hub";
				}
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
