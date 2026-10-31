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

function task(id: string, phase: string, status: string) {
	return {
		id,
		subject: id,
		title: `Task ${id}`,
		phase,
		status,
		wave: 1,
		depends_on: [],
		waits_on: [],
	};
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
			effort: "dashboard",
			phases: [
				{
					subject: "alpha",
					title: "Alpha",
					ordinal: 1,
					state: "in_progress",
					done: 1,
					total: 2,
				},
				{
					subject: "beta",
					title: "Beta",
					ordinal: 2,
					state: "planned",
					done: 1,
					total: 4,
				},
			],
			tasks: [
				task("a-run", "alpha", "running"),
				task("a-done", "alpha", "done"),
				task("b-run", "beta", "running"),
				task("b-ready", "beta", "ready"),
				task("b-wait", "beta", "waiting"),
				task("b-done", "beta", "done"),
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
			if (url.includes("/api/phase")) {
				return json({
					tabs: ["overview", "tasks"],
					detail: {
						subject: "beta",
						title: "Beta",
						effort: "dashboard",
						state: "planned",
						body: "Beta notes",
						tasks: [],
					},
				});
			}
			if (url.includes("/api/task?")) {
				return json({
					detail: { id: "b-run", subject: "b-run", title: "Task b-run" },
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

const PAGE = "#/phase/dashboard/beta";

function taskIds(): string[] {
	return [
		...document.querySelectorAll("main [data-phase-page] [data-task]"),
	].map((el) => el.getAttribute("data-task") ?? "");
}

function triggers(): HTMLElement[] {
	return [
		...document.querySelectorAll<HTMLElement>(
			"main [data-phase-page] [data-status-tabs] [data-tab]",
		),
	];
}

describe("status tabs", () => {
	it("R14 the status tabs are shadcn tab triggers that keep their data-tab attribute", async () => {
		await mountApp(PAGE);
		const list = document.querySelector(
			"main [data-phase-page] [data-status-tabs]",
		);
		expect(list?.getAttribute("data-slot")).toBe("tabs-list");
		expect(list?.getAttribute("data-variant")).toBe("line");
		const tabs = triggers();
		expect(tabs.map((el) => el.getAttribute("data-tab"))).toEqual([
			"active",
			"running",
			"ready",
			"waiting",
			"done",
			"all",
		]);
		for (const tab of tabs) {
			expect(tab.getAttribute("data-slot")).toBe("tabs-trigger");
			expect(tab.getAttribute("role")).toBe("tab");
		}
		expect(
			tabs.filter((el) => el.getAttribute("aria-selected") === "true"),
		).toHaveLength(1);
	});

	it("R15 a click on a status tab shows the tasks of that tab", async () => {
		await mountApp(PAGE);
		expect(taskIds()).toEqual(["b-run", "b-ready", "b-wait"]);
		const pick = async (name: string) => {
			triggers()
				.find((el) => el.getAttribute("data-tab") === name)
				?.click();
			await settle();
		};
		await pick("done");
		expect(taskIds()).toEqual(["b-done"]);
		expect(
			triggers()
				.filter((el) => el.getAttribute("data-state") === "active")
				.map((el) => el.getAttribute("data-tab")),
		).toEqual(["done"]);
		await pick("ready");
		expect(taskIds()).toEqual(["b-ready"]);
		await pick("all");
		expect(taskIds()).toEqual(["b-run", "b-ready", "b-wait", "b-done"]);
	});
});
