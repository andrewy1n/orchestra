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

describe("hub route", () => {
	it("R1 an empty hash shows the work hub", async () => {
		await mountApp("");
		expect(document.querySelector("main [data-hub]")).not.toBeNull();
		expect(document.querySelector("[data-product-index]")).toBeNull();
	});

	it("R1 #/areas shows the product index and not the hub", async () => {
		await mountApp("#/areas");
		expect(document.querySelector("main")?.getAttribute("data-route")).toBe(
			"areas",
		);
		expect(document.querySelector("main [data-product-index]")).not.toBeNull();
		expect(document.querySelector("[data-hub]")).toBeNull();
	});

	it("R1 #/effort/<name> still renders the effort screen", async () => {
		await mountApp("#/effort/dashboard");
		expect(document.querySelector("[data-effort-title]")).not.toBeNull();
		expect(document.querySelector("[data-hub]")).toBeNull();
	});

	it("R1 #/phase/<effort>/<phase> still renders the phase page", async () => {
		await mountApp("#/phase/dashboard/phase-overview");
		expect(document.querySelector("main [data-phase-page]")).not.toBeNull();
		expect(document.querySelector("[data-hub]")).toBeNull();
	});
});
