// @vitest-environment jsdom

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defaultStatusTab } from "./efforts";
import type { EffortView, Snapshot, StatusTab } from "./types";
import { TOKEN_POLL_MS } from "./types";

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

const phasePayload = {
	tabs: ["overview", "tasks"],
	detail: {
		subject: "polish",
		title: "Polish",
		effort: "dashboard",
		state: "in_progress",
		body: "",
		tasks: [],
	},
};

function task(id: string, status: string) {
	return {
		id,
		subject: id,
		title: id,
		phase: "polish",
		status,
		depends_on: [],
		waits_on: [],
	};
}

function effort(statuses: string[]): EffortView {
	return {
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
				total: statuses.length,
			},
		],
		tasks: statuses.map((status, index) => task(`t${index}`, status)),
		needs_you: [],
		backlog: [],
		position: "",
	} as unknown as EffortView;
}

function snapshot(statuses: string[], token: string): Snapshot {
	return {
		token,
		efforts: [effort(statuses)],
		generated_at: "2026-01-01T00:00:00Z",
	} as unknown as Snapshot;
}

function serve(current: { snap: Snapshot }) {
	vi.stubGlobal(
		"fetch",
		vi.fn(async (input: RequestInfo | URL) => {
			const url = String(input);
			const body = url.includes("/api/token")
				? { token: current.snap.token }
				: url.includes("/api/phase")
					? phasePayload
					: current.snap;
			return new Response(JSON.stringify(body), {
				status: 200,
				headers: { "content-type": "application/json" },
			});
		}),
	);
}

async function settle() {
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
}

async function openPhase() {
	const module = await import("./App.svelte");
	mounted = mount(module.default as Component, { target: document.body });
	window.location.hash = "#/phase/dashboard/polish";
	window.dispatchEvent(new HashChangeEvent("hashchange"));
	await settle();
	await settle();
}

function selectedTab(): string | null {
	return (
		document
			.querySelector('[data-status-tabs] [data-state="active"]')
			?.getAttribute("data-tab") ?? null
	);
}

function click(name: StatusTab) {
	const trigger = document.querySelector(
		`[data-status-tabs] [data-tab="${name}"]`,
	) as HTMLElement;
	trigger.dispatchEvent(
		new MouseEvent("mousedown", { bubbles: true, cancelable: true, button: 0 }),
	);
	trigger.click();
	flushSync();
}

describe("defaultStatusTab", () => {
	const none = { active: 0, running: 0, ready: 0, waiting: 0, done: 0, all: 0 };

	it("R4 picks Done when only done tasks exist", () => {
		expect(defaultStatusTab({ ...none, done: 2, all: 2 })).toBe("done");
	});

	it("R5 picks Active when any active task exists", () => {
		expect(
			defaultStatusTab({ ...none, active: 1, ready: 1, done: 3, all: 4 }),
		).toBe("active");
	});

	it("R4 falls back to All for an empty phase", () => {
		expect(defaultStatusTab(none)).toBe("all");
	});
});

describe("phase page status tab", () => {
	it("R4 opens on Done when the phase has no active tasks", async () => {
		serve({ snap: snapshot(["done", "done"], "tok-1") });
		await openPhase();
		expect(selectedTab()).toBe("done");
	});

	it("R5 opens on Active when the phase has an active task", async () => {
		serve({ snap: snapshot(["done", "ready"], "tok-1") });
		await openPhase();
		expect(selectedTab()).toBe("active");
	});

	it("R6 keeps a clicked tab after the phase data refreshes", async () => {
		const current = { snap: snapshot(["done", "done"], "tok-1") };
		serve(current);
		await openPhase();
		click("all");
		expect(selectedTab()).toBe("all");
		current.snap = snapshot(["done", "done", "ready"], "tok-2");
		await vi.advanceTimersByTimeAsync(TOKEN_POLL_MS + 10);
		flushSync();
		await settle();
		expect(selectedTab()).toBe("all");
	});
});
