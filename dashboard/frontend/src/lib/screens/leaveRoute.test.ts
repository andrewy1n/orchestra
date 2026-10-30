// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { needsHref, taskHref } from "../../detail";
import type { DeepPartial, EffortView, Snapshot } from "../../types";

let mounted: ReturnType<typeof mount> | undefined;

function resetDocument() {
	if (mounted) {
		unmount(mounted);
		mounted = undefined;
	}
	document.body.innerHTML = "";
}

beforeEach(() => {
	resetDocument();
	window.location.hash = "";
	vi.useFakeTimers();
});

afterEach(() => {
	resetDocument();
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
		effort({ effort: "invoices" }),
		effort({
			effort: "refunds",
			phases: [
				{
					subject: "caps",
					title: "Caps",
					ordinal: 1,
					state: "in_progress",
					done: 0,
					total: 1,
				},
			],
			tasks: [
				{
					id: "t-cap",
					phase: "caps",
					subject: "t-cap",
					title: "Cap",
					status: "ready",
				},
			],
			needs_you: [
				{
					kind: "blocking-question",
					id: "q1",
					subject: "which-cap",
					text: "which cap",
				},
			],
		}),
	],
} as Snapshot;

const needsPayload = {
	item: {
		kind: "blocking-question",
		id: "q1",
		subject: "which-cap",
		text: "which cap",
		revision: "sha256:abc",
		approval: {
			confirm_choices: [
				{ action: "approve", label: "Approve", note_required: false },
			],
		},
	},
};

function json(body: unknown): Response {
	return new Response(JSON.stringify(body), {
		status: 200,
		headers: { "content-type": "application/json" },
	});
}

function stubFetch() {
	vi.stubGlobal(
		"fetch",
		vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
			const url = String(input);
			if ((init?.method || "GET").toUpperCase() === "POST") {
				return json({ ok: true });
			}
			if (url.includes("/api/token")) return json({ token: snapshot.token });
			if (url.includes("/api/areas")) return json([]);
			if (url.includes("/api/journal")) return json({ open: [], rest: [] });
			if (url.includes("/api/needs?")) return json(needsPayload);
			if (url.includes("/api/task?")) {
				return json({
					detail: { id: "t-cap", subject: "t-cap", title: "Cap" },
				});
			}
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

function clickBack() {
	const back = document.querySelector<HTMLButtonElement>(
		'[data-act="close-detail"]',
	);
	expect(back).toBeTruthy();
	back!.click();
}

describe("leaving an overlay from a fresh load", () => {
	it("R18 a task deep link of a later effort closed with Back ends on its phase page", async () => {
		await mountAt(taskHref("t-cap"));
		clickBack();
		await settle();
		expect(window.location.hash).toBe("#/phase/refunds/caps");
	});

	it("R18 an approved needs item of a later effort ends on that effort", async () => {
		await mountAt(needsHref("refunds", "q1"));
		const approve = document.querySelector<HTMLButtonElement>(
			'[data-write-action="approve"]',
		);
		expect(approve).toBeTruthy();
		approve!.click();
		await settle();
		document.querySelector<HTMLButtonElement>("[data-confirm-submit]")!.click();
		await settle();
		expect(window.location.hash).toBe("#/effort/refunds");
	});
});
