import { getJson } from "../../api";
import type { AreasResponse } from "../../api-types";
import { areaSubject } from "../../router";
import { polling } from "./polling.svelte";
import { navigation } from "./route.svelte";

class AreasState {
	items = $state<AreasResponse>([]);
	loaded = $state(false);
	error = $state("");

	subject = $derived(areaSubject(navigation.route));

	current = $derived(this.items.find((area) => area.subject === this.subject));

	reset() {
		this.items = [];
		this.loaded = false;
		this.error = "";
	}
}

export const areas = new AreasState();

/** Reloads GET /api/areas whenever the snapshot token changes. */
export function bindAreas() {
	areas.reset();

	$effect(() => {
		if (!polling.snapshot?.token) return;
		let cancelled = false;
		void getJson<AreasResponse>("areas")
			.then((data) => {
				if (cancelled) return;
				areas.items = Array.isArray(data) ? data : [];
				areas.loaded = true;
				areas.error = "";
			})
			.catch((err: unknown) => {
				if (cancelled) return;
				areas.loaded = true;
				areas.error = err instanceof Error ? err.message : String(err);
			});
		return () => {
			cancelled = true;
		};
	});
}
