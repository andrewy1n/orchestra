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
		phases: [
			{
				subject: "phase-overview",
				title: "Phase overview UI",
				ordinal: 1,
				state: "in_progress",
				done: 1,
				total: 2,
			},
		],
		tasks: [],
		needs_you: [],
		backlog: [],
		...partial,
	} as EffortView;
}

const snapshot = {
	token: "tok-1",
	generated_at: "2026-01-01T00:00:00Z",
	efforts: [effort({ effort: "dashboard", area: "billing" })],
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

const phasePayload = {
	tabs: ["overview", "spec", "tasks"],
	detail: {
		subject: "phase-overview",
		title: "Phase overview UI",
		effort: "dashboard",
		state: "in_progress",
		body: "Phase notes body",
		spec_body: "",
		tasks: [],
		evidence: { stage: "verify", weight: "full", requirements: [] },
	},
};

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
	vi.stubGlobal(
		"fetch",
		vi.fn(async (input: RequestInfo | URL) => {
			const url = String(input);
			if (url.includes("/api/token")) return json({ token: snapshot.token });
			if (url.includes("/api/areas")) return json(areas);
			if (url.includes("/api/hub")) return json({ items: [] });
			if (url.includes("/api/journal")) return json({ open: [], rest: [] });
			if (url.includes("/api/phase")) return json(phasePayload);
			return json(snapshot);
		}),
	);
	window.location.hash = hash;
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

describe("top tabs", () => {
	function tabs(): { label: string; href: string | null; current: boolean }[] {
		return [...document.querySelectorAll("[data-top-tabs] a")].map((a) => ({
			label: a.textContent?.trim() ?? "",
			href: a.getAttribute("href"),
			current: a.getAttribute("aria-current") === "page",
		}));
	}

	it("R1 the top bar has a Work tab and a Product tab", async () => {
		await mountApp("");
		expect(tabs().map(({ label, href }) => ({ label, href }))).toEqual([
			{ label: "Work", href: "#/" },
			{ label: "Product", href: "#/areas" },
		]);
	});

	it("R1 the Work tab is current on the hub", async () => {
		await mountApp("");
		expect(tabs().map((tab) => tab.current)).toEqual([true, false]);
	});

	it("R1 the Product tab is current on the areas page and below it", async () => {
		await mountApp("#/areas");
		expect(tabs().map((tab) => tab.current)).toEqual([false, true]);
		unmount(mounted as ReturnType<typeof mount>);
		mounted = undefined;
		document.body.innerHTML = "";
		await mountApp("#/effort/dashboard");
		expect(tabs().map((tab) => tab.current)).toEqual([false, true]);
	});

	it("R1 the hub has no breadcrumb and no Areas link of its own", async () => {
		await mountApp("");
		expect(document.querySelector("[data-breadcrumb]")).toBeNull();
		expect(
			document.querySelector("main [data-hub] a[href='#/areas']"),
		).toBeNull();
	});
});
