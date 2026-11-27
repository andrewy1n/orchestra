// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ArchitectureResponse } from "../../api-types";

let mounted: ReturnType<typeof mount> | undefined;

beforeEach(() => {
	document.body.innerHTML = "";
	window.location.hash = "";
	vi.useFakeTimers();
});

afterEach(() => {
	if (mounted) unmount(mounted);
	mounted = undefined;
	document.body.innerHTML = "";
	vi.useRealTimers();
	vi.unstubAllGlobals();
	vi.restoreAllMocks();
});

const view: ArchitectureResponse = {
	revision: "a".repeat(40),
	areas: [
		{
			name: "composer",
			components: [
				{
					name: "records",
					responsibility: "Owns record data.",
					interfaces: ["record-api"],
					decisions: [
						{
							title: "typed-records",
							rationale: "Keeps reads cheap.",
							status: "accepted",
						},
					],
					constraints: [
						{
							name: "adapters-only",
							rule: "Only adapters touch the store.",
							check: "scripts/check-adapters",
							outcome: "unverified",
							constraint_id: "1",
							revision: "a".repeat(40),
						},
					],
				},
			],
		},
	],
	interfaces: [
		{
			name: "record-api",
			provides: "Serves record callers.",
			connects: ["records"],
			decisions: [],
			constraints: [],
		},
	],
};

const empty: ArchitectureResponse = { revision: "", areas: [], interfaces: [] };

function json(body: unknown): Response {
	return new Response(JSON.stringify(body), {
		status: 200,
		headers: { "content-type": "application/json" },
	});
}

async function settle() {
	for (let i = 0; i < 4; i += 1) {
		await vi.advanceTimersByTimeAsync(0);
		flushSync();
	}
}

async function mountApp(
	body: ArchitectureResponse,
	status = 200,
	hash = "#/architecture",
) {
	const urls: string[] = [];
	vi.stubGlobal(
		"fetch",
		vi.fn(async (input: RequestInfo | URL) => {
			const url = String(input);
			urls.push(url);
			if (url.includes("/api/token")) return json({ token: "tok-1" });
			if (url.includes("/api/architecture")) {
				return status === 200 ? json(body) : new Response("failed", { status });
			}
			if (url.includes("/api/areas")) return json([]);
			if (url.includes("/api/product"))
				return json({ statement: null, capabilities: [], goals: [] });
			if (url.includes("/api/journal")) return json({ open: [], rest: [] });
			return json({
				token: "tok-1",
				generated_at: "2026-01-01T00:00:00Z",
				efforts: [],
			});
		}),
	);
	window.location.hash = hash;
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
	return urls;
}

function text(selector: string): string | undefined {
	return document.querySelector(selector)?.textContent?.trim();
}

describe("architecture screen", () => {
	it("R11 shows components, interfaces, decisions and constraints", async () => {
		await mountApp(view);
		expect(text("[data-architecture-component=records] p")).toBe(
			"Owns record data.",
		);
		expect(text("[data-architecture-decision=typed-records]")).toContain(
			"Keeps reads cheap.",
		);
		expect(
			text(
				"[data-architecture-constraint=adapters-only] [data-constraint-outcome]",
			),
		).toBe("unverified");
		expect(
			text(
				"[data-architecture-interface=record-api] [data-interface-connects]",
			),
		).toBe("Connects: records");
	});

	it("R11 says so when no component exists", async () => {
		await mountApp(empty);
		expect(document.querySelector("[data-architecture-empty]")).not.toBeNull();
	});

	it("R11 passes the scope in the route to the endpoint", async () => {
		const urls = await mountApp(view, 200, "#/architecture/component/records");
		expect(
			urls.some((url) => url.includes("/api/architecture?component=records")),
		).toBe(true);
	});

	it("shows the error and no stale view when the fetch fails", async () => {
		await mountApp(view, 500);
		expect(document.querySelector("[data-architecture-error]")).not.toBeNull();
		expect(document.querySelector("[data-architecture-component]")).toBeNull();
	});
});
