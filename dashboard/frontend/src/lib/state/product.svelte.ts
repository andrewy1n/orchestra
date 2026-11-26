import { getJson } from "../../api";
import type { ProductResponse } from "../../api-types";
import { polling } from "./polling.svelte";
import { navigation } from "./route.svelte";

class ProductState {
	overview = $state<ProductResponse | null>(null);
	loaded = $state(false);
	error = $state("");

	reset() {
		this.overview = null;
		this.loaded = false;
		this.error = "";
	}
}

export const product = new ProductState();

function isOverview(data: unknown): data is ProductResponse {
	if (typeof data !== "object" || data === null) return false;
	const body = data as Record<string, unknown>;
	return Array.isArray(body.capabilities) && Array.isArray(body.goals);
}

/** Reloads GET /api/product whenever the snapshot token changes. */
export function bindProduct() {
	product.reset();
	const active = $derived(navigation.route.name === "areas");

	$effect(() => {
		if (!active || !polling.snapshot?.token) return;
		let cancelled = false;
		void getJson<ProductResponse>("product")
			.then((data) => {
				if (cancelled) return;
				product.loaded = true;
				if (isOverview(data)) {
					product.overview = data;
					product.error = "";
				} else {
					product.overview = null;
					product.error = "Product response is malformed";
				}
			})
			.catch((err: unknown) => {
				if (cancelled) return;
				product.loaded = true;
				product.error = err instanceof Error ? err.message : String(err);
			});
		return () => {
			cancelled = true;
		};
	});
}
