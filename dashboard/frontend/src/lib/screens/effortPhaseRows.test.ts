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
				{
					subject: "remind",
					title: "Remind payers",
					ordinal: 3,
					state: "planned",
					done: 0,
					total: 0,
				},
			],
			tasks: [
				{
					id: "t1",
					subject: "t1",
					title: "Render PDF",
					phase: "send",
					status: "running",
					wave: 1,
					depends_on: [],
					waits_on: [],
				},
			],
		}),
	],
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
	vi.stubGlobal(
		"fetch",
		vi.fn(async (input: RequestInfo | URL) => {
			const url = String(input);
			if (url.includes("/api/token")) return json({ token: snapshot.token });
			if (url.includes("/api/areas")) return json([]);
			if (url.includes("/api/journal")) return json({ open: [], rest: [] });
			return json(snapshot);
		}),
	);
	window.location.hash = hash;
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

function rows(): HTMLElement[] {
	return [...document.querySelectorAll<HTMLElement>("main [data-phase-row]")];
}

describe("effort page phase rows", () => {
	it("R21 the effort page lists the phases as rows with a progress bar", async () => {
		await mountApp("#/effort/invoicing");
		expect(rows().map((el) => el.getAttribute("data-phase-row"))).toEqual([
			"draft",
			"send",
			"remind",
		]);
		for (const row of rows()) {
			expect(
				row.querySelector('progress, [role="progressbar"]'),
				row.getAttribute("data-phase-row") ?? "",
			).not.toBeNull();
		}
		expect(rows().map((el) => el.textContent)).toEqual([
			expect.stringContaining("Draft invoices"),
			expect.stringContaining("Send invoices"),
			expect.stringContaining("Remind payers"),
		]);
	});

	it("R22 a phase row links to the phase page", async () => {
		await mountApp("#/effort/invoicing");
		const hrefs = rows().map((row) =>
			(row.closest("a") ?? row.querySelector("a"))?.getAttribute("href"),
		);
		expect(hrefs).toEqual([
			"#/phase/invoicing/draft",
			"#/phase/invoicing/send",
			"#/phase/invoicing/remind",
		]);
	});

	it("R23 the effort page has no task table", async () => {
		await mountApp("#/effort/invoicing");
		expect(document.querySelector("main [data-effort-title]")).not.toBeNull();
		expect(document.querySelector("[data-task-table]")).toBeNull();
		expect(document.querySelector("main [data-task]")).toBeNull();
	});

	it("R24 the effort page has no status tabs", async () => {
		await mountApp("#/effort/invoicing");
		expect(document.querySelector("main [data-effort-title]")).not.toBeNull();
		expect(document.querySelector("[data-status-tabs]")).toBeNull();
		expect(document.querySelector("main [data-tab]")).toBeNull();
	});
});
