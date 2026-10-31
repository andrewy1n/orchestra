// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AreasResponse } from "../../api-types";
import { areaHref, effortHref } from "../../detail";
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
			needs_you: [need("n1", "needs-human on p1: Confirm the tax rate")],
			backlog: [{ id: "b1", subject: "b1", text: "Backlog item" }],
		}),
		effort({ effort: "refunds", kind: "repair" }),
	],
} as Snapshot;

const areas: AreasResponse = [
	{
		subject: "billing",
		title: "Billing",
		scope: "Invoices and payment flows.",
		open_count: 0,
		ideas: [],
	},
];

function json(body: unknown): Response {
	return new Response(JSON.stringify(body), {
		status: 200,
		headers: { "content-type": "application/json" },
	});
}

function stubFetch() {
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

async function mountAt(hash: string) {
	stubFetch();
	window.location.hash = hash;
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

const SIDE_PANELS = [
	"[data-side-needs]",
	"[data-side-backlog]",
	"[data-side-journal-teaser]",
];

describe("side panels by level", () => {
	it("R15 the product index has no side panels", async () => {
		await mountAt("#/");
		expect(document.querySelector("[data-product-index]")).toBeTruthy();
		for (const selector of SIDE_PANELS) {
			expect(document.querySelector(selector)).toBeNull();
		}
		expect(document.querySelector("aside.side")).toBeNull();
	});

	it("R15 the area page has no side panels and one Needs-you list", async () => {
		await mountAt(areaHref("billing"));
		expect(document.querySelector("[data-area-screen]")).toBeTruthy();
		for (const selector of SIDE_PANELS) {
			expect(document.querySelector(selector)).toBeNull();
		}
		expect(document.querySelectorAll("[data-area-needs]")).toHaveLength(1);
		expect(document.querySelector("aside.side")).toBeNull();
	});

	it("R15 the effort page still renders the side panels", async () => {
		await mountAt(effortHref("refunds"));
		for (const selector of SIDE_PANELS) {
			expect(document.querySelector(selector)).toBeTruthy();
		}
	});
});
