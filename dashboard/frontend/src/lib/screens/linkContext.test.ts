// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
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
		goal: "Ship invoicing",
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

const snapshot = {
	token: "tok-1",
	generated_at: "2026-01-01T00:00:00Z",
	efforts: [
		effort({
			effort: "invoicing",
			phases: [
				{
					subject: "draft",
					title: "Draft invoices",
					ordinal: 1,
					state: "done",
					done: 2,
					total: 2,
				},
				{
					subject: "send",
					title: "Send invoices",
					ordinal: 2,
					state: "in_progress",
					done: 1,
					total: 4,
				},
			],
			needs_you: [
				{
					kind: "needs-human",
					id: "n1",
					subject: "r3-unmet",
					text: "needs-human on send: R3 is not met yet",
				},
			],
		}),
	],
} as Snapshot;

const needsPayload = {
	item: {
		kind: "needs-human",
		id: "n1",
		subject: "r3-unmet",
		text: "needs-human on send: R3 is not met yet",
		body: "Check R3 before the release goes out.",
		revision: "sha256:abc",
		approval: { confirm_choices: [] },
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
			if (url.includes("/api/areas")) return json([]);
			if (url.includes("/api/journal")) return json({ open: [], rest: [] });
			if (url.includes("/api/needs?")) return json(needsPayload);
			return json(snapshot);
		}),
	);
	window.location.hash = hash;
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

const wanted = "#/requirement/invoicing/send/R3";

describe("link context without a route phase", () => {
	it("R25 a bare requirement id in a Needs you claim on the effort page links to the default phase", async () => {
		await mountApp("#/effort/invoicing");
		const row = document.querySelector<HTMLElement>('main [data-needs="n1"]');
		expect(row).not.toBeNull();
		expect(row?.querySelector("a")?.getAttribute("href")).toBe(wanted);
	});

	it("R25 a bare requirement id in a needs modal links to the default phase", async () => {
		await mountApp("#/needs/invoicing/n1");
		const body = document.querySelector<HTMLElement>(
			'[data-detail="needs"] [data-detail-section="body"]',
		);
		expect(body).not.toBeNull();
		expect(body?.querySelector("a")?.getAttribute("href")).toBe(wanted);
	});
});
