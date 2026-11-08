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

async function settle() {
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
}

describe("hub payload guard", () => {
	it("R1 a body that is not a hub response leaves the hub empty without throwing", async () => {
		vi.stubGlobal(
			"fetch",
			vi.fn(async (input: RequestInfo | URL) => {
				const url = String(input);
				if (url.includes("/api/token")) return json({ token: snapshot.token });
				if (url.includes("/api/hub")) return json([]);
				if (url.includes("/api/areas")) return json([]);
				return json(snapshot);
			}),
		);
		const { hub } = await import("../state/hub.svelte");
		const module = await import("../../App.svelte");
		mounted = mount(module.default as Component, { target: document.body });
		await settle();

		expect(document.querySelector("main [data-hub]")).not.toBeNull();
		expect(hub.data).toBeNull();
		expect(hub.error).toBe("Hub response is not a hub");
	});
});
