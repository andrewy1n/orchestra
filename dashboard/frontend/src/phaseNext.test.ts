// @vitest-environment jsdom
import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { buildPhaseChrome } from "./phaseChrome";
import type { EffortView, Snapshot } from "./types";

let mounted: ReturnType<typeof mount> | undefined;

beforeEach(() => {
	document.body.innerHTML = "";
	window.location.hash = "";
	vi.useFakeTimers();
});

afterEach(() => {
	if (mounted) {
		unmount(mounted);
		mounted = undefined;
	}
	document.body.innerHTML = "";
	vi.useRealTimers();
	vi.unstubAllGlobals();
	vi.restoreAllMocks();
});

function payload(state: string, statuses: string[], extra = {}) {
	return {
		detail: {
			state,
			tasks: statuses.map((status, index) => ({ id: `t${index}`, status })),
			...extra,
		},
	};
}

describe("phase Next line", () => {
	it("R7 derives the text from this phase when no next field is set", () => {
		const chrome = buildPhaseChrome(payload("in_progress", ["done", "ready"]));
		expect(chrome.nextAction).toBe("Continue ready work");
	});

	it("R7 prefers the payload next fields", () => {
		const chrome = buildPhaseChrome(
			payload("in_progress", ["ready"], { next_action: "Ship it" }),
		);
		expect(chrome.nextAction).toBe("Ship it");
	});

	it("R8 reads Phase complete for a done phase", () => {
		const chrome = buildPhaseChrome(payload("done", ["done", "done"]));
		expect(chrome.nextAction).toBe("Phase complete");
	});
});

const EFFORT_POSITION = "Settled and planned: executing wave 2 now";

const pagePhasePayload = {
	tabs: ["overview", "tasks"],
	detail: {
		subject: "polish",
		title: "Polish",
		effort: "dashboard",
		state: "in_progress",
		body: "",
		tasks: [{ id: "t0", subject: "t0", title: "t0", status: "ready" }],
	},
};

const pageSnapshot = {
	token: "tok-1",
	generated_at: "2026-01-01T00:00:00Z",
	efforts: [
		{
			effort: "dashboard",
			goal: "",
			kind: "deliver",
			finished: false,
			phases: [
				{
					subject: "polish",
					title: "Polish",
					ordinal: 1,
					state: "in_progress",
					done: 0,
					total: 1,
				},
			],
			tasks: [
				{
					id: "t0",
					subject: "t0",
					title: "t0",
					phase: "polish",
					status: "ready",
					depends_on: [],
					waits_on: [],
				},
			],
			needs_you: [],
			backlog: [],
			position: EFFORT_POSITION,
		},
	] as unknown as EffortView[],
} as unknown as Snapshot;

describe("phase page Next line", () => {
	it("R7 does not contain the effort position text", async () => {
		vi.stubGlobal(
			"fetch",
			vi.fn(async (input: RequestInfo | URL) => {
				const url = String(input);
				const body = url.includes("/api/token")
					? { token: pageSnapshot.token }
					: url.includes("/api/phase")
						? pagePhasePayload
						: pageSnapshot;
				return new Response(JSON.stringify(body), {
					status: 200,
					headers: { "content-type": "application/json" },
				});
			}),
		);
		const module = await import("./App.svelte");
		mounted = mount(module.default as Component, { target: document.body });
		window.location.hash = "#/phase/dashboard/polish";
		window.dispatchEvent(new HashChangeEvent("hashchange"));
		await vi.advanceTimersByTimeAsync(0);
		flushSync();
		await vi.advanceTimersByTimeAsync(0);
		flushSync();
		const next = document.querySelector("[data-phase-next]");
		expect(next).not.toBeNull();
		expect(next?.textContent).toContain("Continue ready work");
		expect(next?.textContent).not.toContain(EFFORT_POSITION);
	});
});
