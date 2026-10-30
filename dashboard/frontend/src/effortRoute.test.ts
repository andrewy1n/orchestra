// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { effortHref } from "./detail";
import { effortName, parseRoute } from "./router";
import type { DeepPartial, EffortView, Snapshot } from "./types";

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
		effort({ effort: "dashboard", goal: "Dashboard goal" }),
		effort({ effort: "web", goal: "Web goal" }),
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
	const module = await import("./App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	await settle();
}

function title(): string {
	return (
		document.querySelector("[data-effort-title]")?.textContent?.trim() ?? ""
	);
}

describe("effort route", () => {
	it("R18 #/effort/<name> shows the Home screen of that effort", async () => {
		await mountApp(effortHref("web"));
		expect(title()).toBe("web");
		expect(document.querySelector("[data-goal]")?.textContent).toBe("Web goal");

		window.location.hash = effortHref("dashboard");
		window.dispatchEvent(new HashChangeEvent("hashchange"));
		await settle();
		expect(title()).toBe("dashboard");
	});

	it("the effort route resolves its name from the hash", () => {
		const route = parseRoute(effortHref("my effort"));
		expect(route.name).toBe("effort");
		expect(effortName(route)).toBe("my effort");
		expect(effortName(parseRoute("#/area/billing"))).toBe("");
	});
});
