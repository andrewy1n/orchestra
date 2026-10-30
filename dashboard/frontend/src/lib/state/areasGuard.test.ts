// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Snapshot } from "../../types";

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

const snapshot = {
	token: "tok-1",
	generated_at: "2026-01-01T00:00:00Z",
	efforts: [],
} as unknown as Snapshot;

function json(body: unknown): Response {
	return new Response(JSON.stringify(body), {
		status: 200,
		headers: { "content-type": "application/json" },
	});
}

describe("areas guard", () => {
	it("R1 a response that is not a list sets the areas error", async () => {
		vi.stubGlobal(
			"fetch",
			vi.fn(async (input: RequestInfo | URL) => {
				const url = String(input);
				if (url.includes("/api/token")) return json({ token: snapshot.token });
				if (url.includes("/api/areas")) return json({ error: "boom" });
				if (url.includes("/api/journal")) return json({ open: [], rest: [] });
				return json(snapshot);
			}),
		);
		const module = await import("../../App.svelte");
		const { areas } = await import("./areas.svelte");
		mounted = mount(module.default as Component, { target: document.body });
		await vi.advanceTimersByTimeAsync(0);
		flushSync();
		await vi.advanceTimersByTimeAsync(0);
		flushSync();

		expect(areas.items).toEqual([]);
		expect(areas.loaded).toBe(true);
		expect(areas.error).not.toBe("");
	});
});
