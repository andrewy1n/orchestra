import { getJson } from "../../api";
import type { ArchitectureResponse } from "../../api-types";
import { architectureScope } from "../../router";
import { polling } from "./polling.svelte";
import { navigation } from "./route.svelte";

class ArchitectureState {
	view = $state<ArchitectureResponse | null>(null);
	loaded = $state(false);
	error = $state("");

	reset() {
		this.view = null;
		this.loaded = false;
		this.error = "";
	}
}

export const architecture = new ArchitectureState();

const SCOPES: ReadonlySet<string> = new Set(["area", "component", "interface"]);

function isView(data: unknown): data is ArchitectureResponse {
	if (typeof data !== "object" || data === null) return false;
	const body = data as Record<string, unknown>;
	return Array.isArray(body.areas) && Array.isArray(body.interfaces);
}

export function architecturePath(
	scope: { kind: string; name: string } | null,
): string {
	if (!scope || !SCOPES.has(scope.kind)) return "architecture";
	return `architecture?${scope.kind}=${encodeURIComponent(scope.name)}`;
}

/** Reloads GET /api/architecture whenever the snapshot token or the scope changes. */
export function bindArchitecture() {
	architecture.reset();
	const active = $derived(navigation.route.name === "architecture");
	const path = $derived(architecturePath(architectureScope(navigation.route)));

	$effect(() => {
		if (!active || !polling.snapshot?.token) return;
		let cancelled = false;
		void getJson<ArchitectureResponse>(path)
			.then((data) => {
				if (cancelled) return;
				architecture.loaded = true;
				if (isView(data)) {
					architecture.view = data;
					architecture.error = "";
				} else {
					architecture.view = null;
					architecture.error = "Architecture response is malformed";
				}
			})
			.catch((err: unknown) => {
				if (cancelled) return;
				architecture.loaded = true;
				architecture.view = null;
				architecture.error = err instanceof Error ? err.message : String(err);
			});
		return () => {
			cancelled = true;
		};
	});
}
