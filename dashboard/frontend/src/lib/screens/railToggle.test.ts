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

function phase(
	subject: string,
	title: string,
	ordinal: number,
	state: string,
): EffortView["phases"][number] {
	return {
		subject,
		title,
		ordinal,
		state,
		done: 0,
		total: 0,
	} as EffortView["phases"][number];
}

function effort(
	partial: DeepPartial<EffortView> & Pick<EffortView, "effort">,
): EffortView {
	return {
		goal: "",
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
			effort: "ledger",
			phases: [
				phase("l1", "Ledger one", 1, "done"),
				phase("l2", "Ledger two", 2, "done"),
				phase("l3", "Ledger three", 3, "done"),
				phase("l4", "Ledger four", 4, "in_progress"),
				phase("l5", "Ledger five", 5, "planned"),
			],
		}),
	],
} as Snapshot;

const areas: AreasResponse = [];

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
			if (url.includes("/api/journal")) return json({ open: [], rest: [] });
			if (url.includes("/api/phase")) {
				const query = new URL(url, "http://localhost").searchParams;
				const subject = query.get("phase") ?? "";
				return json({
					tabs: ["overview", "spec"],
					detail: {
						subject,
						title: subject,
						effort: "ledger",
						state: "planned",
						body: "",
						tasks: [],
					},
				});
			}
			return json(snapshot);
		}),
	);
	window.location.hash = hash;
	const module = await import("../../App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

function toggle(): HTMLButtonElement {
	return document.querySelector<HTMLButtonElement>(
		'nav.rail [data-act="show-done-phases"]',
	)!;
}

describe("rail done toggle", () => {
	it("R18 the closed toggle reads Show N done with the count of hidden done phases", async () => {
		await mountApp("#/phase/ledger/l4");
		expect(toggle().textContent?.trim()).toBe("Show 3 done");
	});

	it("R18 the open toggle reads Hide done", async () => {
		await mountApp("#/phase/ledger/l4");
		toggle().click();
		await settle();
		expect(toggle().textContent?.trim()).toBe("Hide done");
		toggle().click();
		await settle();
		expect(toggle().textContent?.trim()).toBe("Show 3 done");
	});
});
