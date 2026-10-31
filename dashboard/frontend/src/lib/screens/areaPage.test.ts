// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AreasResponse } from "../../api-types";
import { areaHref } from "../../detail";
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

function need(id: string, text: string) {
	return {
		id,
		kind: "needs-human",
		next: "",
		phase: "",
		record_type: "finding",
		requirement: "",
		result: "",
		revision: "",
		status: "open",
		subject: id,
		task_id: "",
		text,
	};
}

function effort(
	partial: DeepPartial<EffortView> & Pick<EffortView, "effort">,
): EffortView {
	return {
		goal: "",
		kind: "deliver",
		finished: false,
		area: "billing",
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
	efforts: [
		effort({
			effort: "invoices",
			goal: "Send invoices",
			needs_you: [need("n1", "needs-human on p1: Confirm the tax rate")],
		}),
		effort({
			effort: "refunds",
			goal: "Refund flow",
			needs_you: [need("n2", "needs-human on p2: Approve the refund cap")],
		}),
		effort({ effort: "search", area: "search", goal: "Search it" }),
	],
} as Snapshot;

const billing = {
	subject: "billing",
	title: "Billing",
	scope: "Invoices and **payment** flows.",
	open_count: 1,
	ideas: [
		{
			subject: "refund-idea",
			text: "Refund idea",
			status: "open",
			area: "billing",
			effort: "",
			phase: "",
		},
		{
			subject: "moved-idea",
			text: "Moved idea",
			status: "promoted",
			area: "billing",
			effort: "invoices",
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
}

async function settle() {
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
}

async function mountArea() {
	stubFetch([billing]);
	window.location.hash = areaHref("billing");
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
	return document.querySelector("[data-area-screen]") as HTMLElement;
}

describe("area page", () => {
	it("R10 each effort of the area is a row that links to its effort page", async () => {
		const screen = await mountArea();
		const rows = [...screen.querySelectorAll("a[data-effort-row]")];
		expect(rows.map((row) => row.getAttribute("data-effort-row"))).toEqual([
			"invoices",
			"refunds",
		]);
		expect(rows.map((row) => row.getAttribute("href"))).toEqual([
			"#/effort/invoices",
			"#/effort/refunds",
		]);
		expect(rows[0]?.textContent).toContain("Send invoices");
	});

	it("R11 the Ideas section lists only the open ideas of the area", async () => {
		const screen = await mountArea();
		const open = screen.querySelector("[data-area-open]");
		expect(
			[...open!.querySelectorAll("[data-idea]")].map((el) =>
				el.getAttribute("data-idea"),
			),
		).toEqual(["refund-idea"]);
		expect(screen.querySelector("[data-effort-row] [data-idea]")).toBeNull();
		expect(
			screen.querySelector("[data-area-efforts]")?.textContent,
		).not.toContain("Moved idea");
		expect(open?.textContent).not.toContain("Moved idea");
	});

	it("R15 one Needs-you list merges the items of every effort in the area", async () => {
		const screen = await mountArea();
		const lists = screen.querySelectorAll("[data-area-needs]");
		expect(lists).toHaveLength(1);
		const rows = lists[0]!.querySelectorAll("[data-area-need]");
		expect([...rows].map((row) => row.getAttribute("data-area-need"))).toEqual([
			"n1",
			"n2",
		]);
		expect(lists[0]?.textContent).not.toContain("Search it");
	});

	it("R16 each Needs-you row names its effort", async () => {
		const screen = await mountArea();
		const rows = [...screen.querySelectorAll("[data-area-need]")];
		expect(rows[0]?.querySelector("[data-need-effort]")?.textContent).toBe(
			"invoices",
		);
		expect(rows[1]?.querySelector("[data-need-effort]")?.textContent).toBe(
			"refunds",
		);
		expect(rows[0]?.textContent).toContain("Confirm the tax rate");
	});

	it("R17 the area page has no Needs-you action buttons", async () => {
		const screen = await mountArea();
		expect(screen.querySelectorAll("[data-area-need]").length).toBe(2);
		expect(screen.querySelector("[data-area-needs] button")).toBeNull();
		expect(screen.querySelector("[data-act]")).toBeNull();
		expect(screen.querySelector("button")).toBeNull();
	});

	it("R31 each Needs-you row links to its effort's page", async () => {
		const screen = await mountArea();
		const rows = [...screen.querySelectorAll("a[data-area-need]")];
		expect(rows.map((row) => row.getAttribute("href"))).toEqual([
			"#/effort/invoices",
			"#/effort/refunds",
		]);
	});
});
