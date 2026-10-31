// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AreasResponse } from "../../api-types";
import type { DeepPartial, EffortView, Snapshot } from "../../types";

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

function effort(
	partial: DeepPartial<EffortView> & Pick<EffortView, "effort">,
): EffortView {
	return {
		goal: "",
		kind: "deliver",
		finished: false,
		area: "",
		phases: [],
		tasks: [],
		needs_you: [],
		backlog: [],
		...partial,
	} as EffortView;
}

function snapshotOf(efforts: EffortView[]): Snapshot {
	return {
		token: "tok-1",
		generated_at: "2026-01-01T00:00:00Z",
		efforts,
	} as Snapshot;
}

const placed = snapshotOf([
	effort({ effort: "invoicing", area: "billing" }),
	effort({ effort: "refunds", area: "billing" }),
	effort({ effort: "web" }),
]);

const allPlaced = snapshotOf([
	effort({ effort: "invoicing", area: "billing" }),
	effort({ effort: "refunds", area: "billing" }),
]);

const areas: AreasResponse = [
	{
		subject: "billing",
		title: "Billing",
		scope: "Invoices and **payment** flows. Refunds live elsewhere.",
		open_count: 3,
		ideas: [],
	},
	{
		subject: "ops",
		title: "Operations",
		scope: "Deploys and on-call",
		open_count: 1,
		ideas: [],
	},
];

function json(body: unknown): Response {
	return new Response(JSON.stringify(body), {
		status: 200,
		headers: { "content-type": "application/json" },
	});
}

async function settle() {
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
}

async function mountApp(snapshot: Snapshot, hash = "") {
	vi.stubGlobal(
		"fetch",
		vi.fn(async (input: RequestInfo | URL) => {
			const url = String(input);
			if (url.includes("/api/token")) return json({ token: snapshot.token });
			if (url.includes("/api/areas")) return json(areas);
			if (url.includes("/api/journal")) return json({ open: [], rest: [] });
			return json(snapshot);
		}),
	);
	window.location.hash = hash;
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

function card(subject: string): Element {
	const found = document.querySelector(`[data-area-card="${subject}"]`);
	expect(found).not.toBeNull();
	return found as Element;
}

describe("product index", () => {
	it("R1 the home route shows the product index with one card for each area", async () => {
		await mountApp(placed);
		const index = document.querySelector("[data-product-index]");
		expect(index).not.toBeNull();
		const cards = index?.querySelectorAll("[data-area-card]") ?? [];
		expect([...cards].map((el) => el.getAttribute("data-area-card"))).toEqual([
			"billing",
			"ops",
		]);
		expect(document.querySelector("[data-effort-title]")).toBeNull();
	});

	it("R2 an area card shows the area title", async () => {
		await mountApp(placed);
		expect(
			card("billing").querySelector("[data-card-title]")?.textContent,
		).toBe("Billing");
		expect(card("ops").querySelector("[data-card-title]")?.textContent).toBe(
			"Operations",
		);
	});

	it("R3 an area card shows the first sentence of the scope", async () => {
		await mountApp(placed);
		const scope = card("billing").querySelector("[data-card-scope]");
		expect(scope?.textContent?.trim()).toBe("Invoices and payment flows.");
		expect(card("billing").textContent).not.toContain("Refunds live elsewhere");
		expect(
			card("ops").querySelector("[data-card-scope]")?.textContent?.trim(),
		).toBe("Deploys and on-call");
	});

	it("R4 an area card shows the number of efforts in the area", async () => {
		await mountApp(placed);
		expect(
			card("billing").querySelector("[data-card-efforts]")?.textContent,
		).toContain("2 efforts");
		expect(
			card("ops").querySelector("[data-card-efforts]")?.textContent,
		).toContain("0 efforts");
	});

	it("R5 an area card shows the number of open ideas in the area", async () => {
		await mountApp(placed);
		expect(
			card("billing").querySelector("[data-card-ideas]")?.textContent,
		).toContain("3 open ideas");
		expect(
			card("ops").querySelector("[data-card-ideas]")?.textContent,
		).toContain("1 open idea");
		expect(
			card("ops").querySelector("[data-card-ideas]")?.textContent,
		).not.toContain("ideas");
	});

	it("R6 an area card does not list effort names", async () => {
		await mountApp(placed);
		expect(card("billing").querySelector("[data-card-effort]")).toBeNull();
		expect(card("billing").textContent).not.toContain("invoicing");
		expect(card("billing").textContent).not.toContain("refunds");
		expect(card("ops").querySelector("[data-card-effort]")).toBeNull();
	});

	it("R7 an area card is one link to the area route", async () => {
		await mountApp(placed);
		const el = card("billing");
		expect(el.tagName).toBe("A");
		expect(el.getAttribute("href")).toBe("#/area/billing");
		expect(el.querySelector("a")).toBeNull();
		expect(card("ops").getAttribute("href")).toBe("#/area/ops");
	});

	it("R8 efforts with no area show under a Not in an area heading", async () => {
		await mountApp(placed);
		const heading = [
			...document.querySelectorAll("[data-product-index] h2"),
		].find((h) => h.textContent?.trim() === "Not in an area");
		expect(heading).toBeTruthy();
		const links = document.querySelectorAll("[data-unplaced] a");
		expect([...links].map((a) => a.textContent?.trim())).toEqual(["web"]);
		expect(links[0]?.getAttribute("href")).toBe("#/effort/web");
		unmount(mounted!);
		mounted = undefined;
		document.body.innerHTML = "";
		await mountApp(allPlaced);
		expect(document.querySelector("[data-product-index]")).not.toBeNull();
		expect(document.querySelector("[data-unplaced]")).toBeNull();
		expect(document.body.textContent).not.toContain("Not in an area");
	});

	it("R30 an area card contains no button", async () => {
		await mountApp(placed);
		const cards = document.querySelectorAll("[data-area-card]");
		expect(cards.length).toBeGreaterThan(0);
		for (const el of cards) {
			expect(el.querySelector("button, [role='button']")).toBeNull();
		}
	});
});
