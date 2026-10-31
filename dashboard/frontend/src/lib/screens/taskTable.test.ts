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

function row(id: string): HTMLElement | null {
	return document.querySelector<HTMLElement>(
		`main [data-phase-page] [data-task-table] [data-task="${id}"]`,
	);
}

describe("task table", () => {
	it("R20 a click on a task row opens the task overlay", async () => {
		await mountApp(PAGE);
		expect(document.querySelector('[role="dialog"]')).toBeNull();
		const target = row("b-run");
		expect(target).not.toBeNull();
		expect(target?.getAttribute("data-phase-of")).toBe("beta");
		target?.click();
		await settle();
		expect(window.location.hash).toBe("#/task/b-run");
		expect(
			document.querySelector('[role="dialog"][data-detail="task"]'),
		).not.toBeNull();
	});

	it("R20 Enter on a focused task row opens the task overlay", async () => {
		await mountApp(PAGE);
		const target = row("b-ready");
		expect(target).not.toBeNull();
		target?.dispatchEvent(
			new KeyboardEvent("keydown", { key: "Enter", bubbles: true }),
		);
		await settle();
		expect(window.location.hash).toBe("#/task/b-ready");
		expect(
			document.querySelector('[role="dialog"][data-detail="task"]'),
		).not.toBeNull();
	});
});
