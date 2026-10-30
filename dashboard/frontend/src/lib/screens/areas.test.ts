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
		expect(document.querySelector("[data-task-table]")).not.toBeNull();
	});

	it("R6 home route lists each area as a card link instead", async () => {
		await mountApp([billing]);
		const cards = document.querySelectorAll("[data-area-card]");
		expect(cards).toHaveLength(1);
		expect(cards[0]?.getAttribute("href")).toBe("#/area/billing");
		expect(document.querySelector("[data-task-table]")).toBeNull();
	});

	it("R7 area screen shows the title, rendered scope and open ideas first", async () => {
		await mountApp([billing], areaHref("billing"));
		const screen = document.querySelector("[data-area-screen]");
		expect(screen).not.toBeNull();
		expect(screen?.textContent).toContain("Billing");
		expect(screen?.querySelector("[data-area-scope] strong")?.textContent).toBe(
			"payment",
		);
		const subjects = [...screen!.querySelectorAll("[data-idea]")].map((el) =>
			el.getAttribute("data-idea"),
		);
		expect(subjects.slice(0, 2)).toEqual(["refund-flow", "invoice-pdf"]);
		const openList = screen?.querySelector("[data-area-open]");
		expect(openList?.querySelectorAll("[data-idea]")).toHaveLength(2);
	});

	it("R8 moved ideas are collapsed and link to their effort or phase", async () => {
		await mountApp([billing], areaHref("billing"));
		const toggle = document.querySelector("[data-area-moved-toggle]");
		expect(toggle?.getAttribute("aria-expanded")).toBe("false");
		const content = document.querySelector("[data-slot='collapsible-content']");
		expect(content?.getAttribute("data-state")).toBe("closed");
		expect(content?.hasAttribute("hidden")).toBe(true);
		(toggle as HTMLElement).click();
		await settle();
		expect(toggle?.getAttribute("aria-expanded")).toBe("true");
		expect(content?.getAttribute("data-state")).toBe("open");
		const phaseLink = document.querySelector('[data-idea-link="phase"]');
		expect(phaseLink?.getAttribute("href")).toBe(
			"#/phase/dashboard/areas-and-ideas",
		);
		const effortLink = document.querySelector('[data-idea-link="effort"]');
		expect(effortLink?.textContent?.trim()).toBe("web");
		(effortLink as HTMLElement).click();
		await settle();
		expect(window.location.hash).toBe("#/effort/web");
		expect(
			document.querySelector("[data-effort-title]")?.textContent?.trim(),
		).toBe("web");
	});

	it("R9 area screen renders no promote or dismiss controls", async () => {
		await mountApp([billing], areaHref("billing"));
		const screen = document.querySelector("[data-area-screen]");
		const labels = [...screen!.querySelectorAll("button")].map(
			(b) => b.textContent ?? "",
		);
		expect(labels.join(" ")).not.toMatch(/promote|dismiss/i);
		expect(screen?.innerHTML).not.toMatch(/promote\b|dismiss/i);
		expect(
			screen?.querySelector("[data-act]:not([data-act='close-area'])"),
		).toBeNull();
	});

	it("R10 router resolves the area hash to the area screen and survives a reload", async () => {
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
			"Billing",
		);
	});
});
