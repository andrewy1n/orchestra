// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { parseRoute } from "../../router";
import type { DeepPartial, EffortView, Snapshot } from "../../types";

let mounted: ReturnType<typeof mount> | undefined;

beforeEach(() => {
	document.body.innerHTML = "";
	window.location.hash = "";
	vi.useFakeTimers();
	if (!globalThis.ResizeObserver) {
		globalThis.ResizeObserver = class {
			observe() {}
			unobserve() {}
			disconnect() {}
		};
	}
	window.matchMedia = (query: string) =>
		({
			matches: false,
			media: query,
			onchange: null,
			addListener() {},
			removeListener() {},
			addEventListener() {},
			removeEventListener() {},
			dispatchEvent() {
				return false;
			},
		}) as MediaQueryList;
});

afterEach(() => {
	if (mounted) unmount(mounted);
	mounted = undefined;
	document.body.innerHTML = "";
	vi.useRealTimers();
	vi.unstubAllGlobals();
	vi.restoreAllMocks();
});

const phasePayload = {
	tabs: ["overview", "spec", "design", "tasks", "evidence"],
	detail: {
		subject: "phase-overview",
		title: "Phase overview UI",
		effort: "dashboard",
		state: "in_progress",
		body: "Phase notes body",
		spec_body: "## Requirements\n\nR1: chrome",
		design_body: "## Architecture\n\nShared chrome",
		awaiting_signoff: false,
		position: "Ship shared chrome",
		tasks: [
			{ id: "t1", subject: "t1", title: "Chrome", status: "done", wave: 1 },
			{ id: "t2", subject: "t2", title: "Tabs", status: "ready", wave: 1 },
			{ id: "t3", subject: "t3", title: "Verify", status: "ready", wave: 2 },
		],
		evidence: {
			stage: "verify",
			weight: "full",
			requirements: [
				{
					id: "R1",
					text: "chips",
					status: "open",
					latest_check: { result: "pass" },
				},
				{
					id: "R5",
					text: "nav",
					status: "open",
					latest_check: { result: "fail" },
				},
			],
		},
	},
};

function effort(
	partial: DeepPartial<EffortView> & Pick<EffortView, "effort">,
): EffortView {
	return {
		goal: "",
		kind: "deliver",
		finished: false,
		area: "",
		phases: [
			{
				subject: "phase-overview",
				title: "Phase overview UI",
				ordinal: 1,
				state: "in_progress",
				done: 1,
				total: 3,
			},
		],
		tasks: [],
		needs_you: [],
		backlog: [],
		position: "Continue phase-overview",
		...partial,
	} as EffortView;
}

const snapshot = {
	token: "tok-1",
	generated_at: "2026-01-01T00:00:00Z",
	efforts: [effort({ effort: "dashboard" })],
} as Snapshot;

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

async function mountApp(hash: string) {
	const fetchMock = vi.fn(
		async (input: RequestInfo | URL, _init?: RequestInit) => {
			const url = String(input);
			if (url.includes("/api/token")) return json({ token: snapshot.token });
			if (url.includes("/api/areas")) return json([]);
			if (url.includes("/api/journal")) return json({ open: [], rest: [] });
			if (url.includes("/api/phase")) return json(phasePayload);
			if (url.includes("/api/requirement")) {
				return json({
					detail: {
						id: "R1",
						text: "chips",
						status: "open",
						phase: "phase-overview",
					},
				});
			}
			return json(snapshot);
		},
	);
	vi.stubGlobal("fetch", fetchMock);
	window.location.hash = hash;
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
	return fetchMock;
}

const PAGE = "#/phase/dashboard/phase-overview";

async function visit(hash: string) {
	window.location.hash = hash;
	window.dispatchEvent(new HashChangeEvent("hashchange"));
	await settle();
}

async function tabsCarrying(selector: string): Promise<string[]> {
	const found: string[] = [];
	for (const tab of phasePayload.tabs) {
		await visit(
			tab === "overview" ? PAGE : `${PAGE}/tab/${encodeURIComponent(tab)}`,
		);
		if (document.querySelector(`main ${selector}`)) found.push(tab);
	}
	return found;
}

describe("phase page", () => {
	it("R1 the phase route renders in the main pane and not in a dialog", async () => {
		await mountApp(PAGE);
		expect(document.querySelector("main [data-phase-page]")).not.toBeNull();
		expect(document.querySelector('[role="dialog"]')).toBeNull();
	});

	it("R4 the header shows the phase title", async () => {
		await mountApp(PAGE);
		expect(
			document.querySelector("main [data-phase-title]")?.textContent?.trim(),
		).toBe("Phase overview UI");
	});

	it("R5 the header shows the phase state", async () => {
		await mountApp(PAGE);
		expect(
			document.querySelector("main [data-phase-state]")?.textContent ?? "",
		).toMatch(/in[ _]progress/i);
	});

	it("R6 the page shows the chips of the phase", async () => {
		await mountApp(PAGE);
		const chips = document.querySelector("main [data-phase-chips]");
		expect(chips).not.toBeNull();
		expect(chips?.textContent ?? "").toMatch(/in progress/i);
		expect(chips?.textContent ?? "").toContain("1/3 tasks");
	});

	it("R7 the page shows the next action of the phase", async () => {
		await mountApp(PAGE);
		expect(
			document.querySelector("main [data-phase-next]")?.textContent ?? "",
		).toContain("Ship shared chrome");
	});

	it("R8 the page shows one button for each requirement", async () => {
		await mountApp(PAGE);
		const buttons = [
			...document.querySelectorAll<HTMLElement>("main [data-phase-req]"),
		];
		expect(buttons.map((el) => el.getAttribute("data-phase-req"))).toEqual([
			"R1",
			"R5",
		]);
		expect(buttons.every((el) => el.tagName === "BUTTON")).toBe(true);
	});

	it("R10 the page shows the tabs of the phase", async () => {
		await mountApp(PAGE);
		const tabs = [...document.querySelectorAll("main [data-phase-tab]")].map(
			(el) => el.getAttribute("data-phase-tab"),
		);
		expect(tabs).toEqual(phasePayload.tabs);
	});

	it("R11 the tab hash opens the page on that tab", async () => {
		const hash = `${PAGE}/tab/spec`;
		const route = parseRoute(hash);
		expect(route.name).toBe("phase");
		expect(route.parts).toEqual([
			"phase",
			"dashboard",
			"phase-overview",
			"tab",
			"spec",
		]);
		await mountApp(hash);
		const selected = [
			...document.querySelectorAll("main [data-phase-tab]"),
		].filter((el) => el.getAttribute("aria-selected") === "true");
		expect(selected.map((el) => el.getAttribute("data-phase-tab"))).toEqual([
			"spec",
		]);
	});

	it("R12 the page shows the task graph on the tab that carries it", async () => {
		await mountApp(PAGE);
		const carrying = await tabsCarrying("[data-task-graph]");
		expect(carrying.length).toBeGreaterThan(0);
	});

	it("R13 the page shows the evidence board on the tab that carries it", async () => {
		await mountApp(PAGE);
		const carrying = await tabsCarrying("[data-evidence-board]");
		expect(carrying.length).toBeGreaterThan(0);
		const board = document.querySelector("main [data-evidence-board]");
		expect(board?.querySelector('[data-evidence-req="R1"]')).not.toBeNull();
		expect(board?.querySelector('[data-evidence-req="R5"]')).not.toBeNull();
	});

	it("R14 the page shows the sections of the phase detail", async () => {
		await mountApp(PAGE);
		expect(
			document.querySelector("main [data-detail-section]")?.textContent ?? "",
		).toContain("Phase notes body");
		await visit(`${PAGE}/tab/spec`);
		expect(
			document.querySelector("main [data-detail-section]")?.textContent ?? "",
		).toContain("Requirements");
		await visit(`${PAGE}/tab/design`);
		expect(
			document.querySelector("main [data-detail-section]")?.textContent ?? "",
		).toContain("Architecture");
	});

	it("R29 the page writes nothing to the store", async () => {
		const fetchMock = await mountApp(PAGE);
		for (const tab of phasePayload.tabs) {
			await visit(`${PAGE}/tab/${tab}`);
		}
		expect(document.querySelector("main [data-phase-page]")).not.toBeNull();
		expect(document.querySelector("main [data-write-action]")).toBeNull();
		const writes = fetchMock.mock.calls.filter(([, init]) => {
			const method = (init?.method ?? "GET").toUpperCase();
			return method !== "GET";
		});
		expect(writes).toEqual([]);
	});
});
