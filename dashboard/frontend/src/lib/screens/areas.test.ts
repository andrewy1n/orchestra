// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AreasResponse } from "../../api-types";
import { areaHref } from "../../detail";
import { parseRoute } from "../../router";
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
		phases: [],
		tasks: [],
		needs_you: [],
		backlog: [],
		...partial,
	} as EffortView;
}

const snapshot = {
	token: "tok-1",
	generated_at: "2026-01-01T00:00:00Z",
	efforts: [effort({ effort: "dashboard" }), effort({ effort: "web" })],
} as Snapshot;

const billing = {
	subject: "billing",
	title: "Billing",
	scope: "Invoices and **payment** flows.",
	open_count: 2,
	ideas: [
		{
			subject: "moved-phase",
			text: "Receipt PDFs",
			status: "promoted",
			area: "billing",
			effort: "dashboard",
			phase: "areas-and-ideas",
		},
		{
			subject: "refund-flow",
			text: "Refund flow",
			status: "open",
			area: "billing",
			effort: "",
			phase: "",
		},
		{
			subject: "moved-effort",
			text: "Tax export",
			status: "promoted",
			area: "billing",
			effort: "web",
			phase: "",
		},
		{
			subject: "invoice-pdf",
			text: "Invoice PDF",
			status: "open",
			area: "billing",
			effort: "",
			phase: "",
		},
	],
};

function json(body: unknown): Response {
	return new Response(JSON.stringify(body), {
		status: 200,
		headers: { "content-type": "application/json" },
	});
}

function stubFetch(areas: AreasResponse) {
	const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
		const url = String(input);
		if (url.includes("/api/token")) return json({ token: snapshot.token });
		if (url.includes("/api/areas")) return json(areas);
		if (url.includes("/api/journal")) return json({ open: [], rest: [] });
		return json(snapshot);
	});
	vi.stubGlobal("fetch", fetchMock);
	return fetchMock;
}

async function settle() {
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
}

async function mountApp(areas: AreasResponse, hash = "") {
	stubFetch(areas);
	window.location.hash = hash;
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

describe("areas", () => {
	it("R6 effort home no longer lists the areas block", async () => {
		await mountApp([billing], "#/effort/dashboard");
		expect(document.querySelector("[data-areas]")).toBeNull();
		expect(document.querySelector("[data-task-table]")).toBeNull();
	});

	it("R6 home route lists each area as a card link instead", async () => {
		await mountApp([billing]);
		const cards = document.querySelectorAll("[data-area-card]");
		expect(cards).toHaveLength(1);
		expect(cards[0]?.getAttribute("href")).toBe("#/area/billing");
		expect(document.querySelector("[data-task-table]")).toBeNull();
	});

	it("area screen renders the scope markdown and the breadcrumb title", async () => {
		await mountApp([billing], areaHref("billing"));
		const screen = document.querySelector("[data-area-screen]");
		expect(screen?.querySelector("[data-area-scope] strong")?.textContent).toBe(
			"payment",
		);
		expect(document.querySelector("[data-breadcrumb]")?.textContent).toContain(
			"Billing",
		);
		expect(screen?.querySelector("[data-area-moved]")).toBeNull();
		expect(screen?.innerHTML).not.toMatch(/promote\b|dismiss/i);
	});

	it("router resolves the area hash to the area screen and survives a reload", async () => {
		const route = parseRoute(areaHref("billing"));
		expect(route.name).toBe("area");
		expect(route.parts).toEqual(["area", "billing"]);
		await mountApp([billing], areaHref("billing"));
		expect(document.querySelector("[data-area-screen]")).not.toBeNull();
		expect(document.querySelector("[data-task-table]")).toBeNull();
		unmount(mounted!);
		mounted = undefined;
		document.body.innerHTML = "";
		await mountApp([billing], areaHref("billing"));
		expect(document.querySelector("[data-area-screen]")?.textContent).toContain(
			"Invoices and",
		);
	});
});
