// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { journalHref, taskHref } from "../../detail";
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
	efforts: [effort({ effort: "invoices" }), effort({ effort: "refunds" })],
} as Snapshot;

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
			if (url.includes("/api/areas")) return json([]);
			if (url.includes("/api/journal")) return json({ open: [], rest: [] });
			if (url.includes("/api/task?")) {
				return json({ detail: { id: "t1", subject: "t1", title: "T1" } });
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

describe("close fallback", () => {
	it("R18 a task deep link closed with Esc ends on the effort page", async () => {
		await mountAt(taskHref("t1"));
		expect(document.querySelector('[data-detail="task"]')).toBeTruthy();

		const target = document.activeElement ?? document.body;
		target.dispatchEvent(
			new KeyboardEvent("keydown", {
				key: "Escape",
				bubbles: true,
				cancelable: true,
			}),
		);
		await settle();

		expect(document.querySelector('[data-detail="task"]')).toBeNull();
		expect(window.location.hash).toBe("#/effort/invoices");
	});

	it("R18 the journal Back button ends on the effort page", async () => {
		await mountAt(journalHref("refunds"));
		const back = document.querySelector<HTMLButtonElement>(
			'[data-act="close-journal"]',
		);
		expect(back).toBeTruthy();

		back!.click();
		await settle();

		expect(window.location.hash).toBe("#/effort/refunds");
	});

	it("R18 Esc on the journal screen ends on the effort page", async () => {
		await mountAt(journalHref("refunds"));

		window.dispatchEvent(
			new KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
		);
		await settle();

		expect(window.location.hash).toBe("#/effort/refunds");
	});
});
