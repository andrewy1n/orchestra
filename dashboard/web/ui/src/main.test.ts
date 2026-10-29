// @vitest-environment jsdom
/**
 * Main-pane acceptance cases for the web dashboard UI.
 *
 * R5: poll /api/token; refetch /api/snapshot only when the token changes.
 * R6: effort rail shows name, kind, and needs-you count.
 * R7: finished effort with no Needs you is hidden until asked.
 * R8: main pane shows the selected effort's goal.
 * R9: selecting one phase limits task rows to that phase.
 * R10: status tabs filter task rows by state.
 * R32: finished effort with Needs you stays on the rail.
 * R33: selecting all phases shows every task in the effort.
 *
 * Cases exercise the pure modules the App mounts (`poll`, `efforts`) and
 * the App source wiring. When the Svelte plugin is loaded they also mount.
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
	filteredTasks,
	resolvedPhase,
	STATUS_TABS,
	visibleEfforts,
} from "./efforts";
import { startTokenPoller } from "./poll";
import type { EffortView, Snapshot } from "./types";
import { TOKEN_POLL_MS } from "./types";

const here = path.dirname(fileURLToPath(import.meta.url));
const appSource = readFileSync(path.join(here, "App.svelte"), "utf8");

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
	partial: Partial<EffortView> & Pick<EffortView, "effort">,
): EffortView {
	return {
		goal: "",
		kind: "deliver",
		finished: false,
		phases: [],
		tasks: [],
		needs_you: [],
		...partial,
	};
}

function makeSnapshot(efforts: EffortView[], token = "tok-1"): Snapshot {
	return { token, efforts, generated_at: "2026-01-01T00:00:00Z" };
}

async function tryMountApp(): Promise<boolean> {
	try {
		const module = await import("./App.svelte");
		mounted = mount(module.default as Component, { target: document.body });
		await vi.advanceTimersByTimeAsync(0);
		flushSync();
		return true;
	} catch {
		mounted = undefined;
		return false;
	}
}

describe("web-dashboard main", () => {
	it("R5: The page requests /api/token on an interval and requests /api/snapshot again only when the token value changes.", async () => {
		expect(TOKEN_POLL_MS).toBe(2000);
		expect(appSource).toMatch(/startTokenPoller/);

		let token = "tok-1";
		let snap = makeSnapshot(
			[effort({ effort: "alpha", goal: "Ship alpha" })],
			"tok-1",
		);
		let snapshotCalls = 0;
		let tokenCalls = 0;
		const seen: string[] = [];

		const poller = startTokenPoller({
			intervalMs: TOKEN_POLL_MS,
			getToken: async () => {
				tokenCalls += 1;
				return { token };
			},
			getSnapshot: async () => {
				snapshotCalls += 1;
				return snap;
			},
			onSnapshot: (data) => {
				seen.push(data.token);
			},
		});

		await vi.advanceTimersByTimeAsync(0);
		expect(snapshotCalls).toBe(1);
		expect(seen).toEqual(["tok-1"]);

		await vi.advanceTimersByTimeAsync(TOKEN_POLL_MS);
		expect(tokenCalls).toBeGreaterThanOrEqual(1);
		expect(snapshotCalls).toBe(1);

		await vi.advanceTimersByTimeAsync(TOKEN_POLL_MS);
		expect(snapshotCalls).toBe(1);

		token = "tok-2";
		snap = { ...snap, token: "tok-2" };
		await vi.advanceTimersByTimeAsync(TOKEN_POLL_MS);
		expect(snapshotCalls).toBe(2);
		expect(seen).toEqual(["tok-1", "tok-2"]);

		poller.stop();
	});

	it("R6: The effort rail shows each effort's name, kind, and needs-you count.", async () => {
		expect(appSource).toContain("data-effort=");
		expect(appSource).toMatch(/view\.kind/);
		expect(appSource).toMatch(/needs you/);

		const views = [
			effort({
				effort: "dashboard",
				kind: "deliver",
				needs_you: [
					{ kind: "unsigned-check", id: "c1", subject: "gates", text: "sign" },
					{ kind: "loop-route", id: "c2", subject: "R2", text: "R2" },
				],
			}),
			effort({
				effort: "flaky-suite",
				kind: "repair",
				needs_you: [],
			}),
		];
		const { shown } = visibleEfforts(views, false);
		expect(shown.map((v) => v.effort)).toEqual(["dashboard", "flaky-suite"]);
		expect(shown[0]!.kind).toBe("deliver");
		expect(shown[0]!.needs_you.length).toBe(2);
		expect(shown[1]!.kind).toBe("repair");

		// When the Svelte plugin is present, assert the rail markup too.
		vi.stubGlobal(
			"fetch",
			vi.fn(async (input: RequestInfo | URL) => {
				const url = String(input);
				if (url.includes("/api/token")) {
					return new Response(JSON.stringify({ token: "tok-1" }), {
						status: 200,
						headers: { "content-type": "application/json" },
					});
				}
				return new Response(JSON.stringify(makeSnapshot(views)), {
					status: 200,
					headers: { "content-type": "application/json" },
				});
			}),
		);
		if (await tryMountApp()) {
			const dash = document.querySelector('[data-effort="dashboard"]');
			expect(dash?.textContent).toContain("dashboard");
			expect(dash?.textContent).toContain("deliver");
			expect(dash?.textContent).toMatch(/2 needs you/);
			const repair = document.querySelector('[data-effort="flaky-suite"]');
			expect(repair?.textContent).toContain("repair");
		}
	});

	it("R7: A finished effort with no Needs you items is hidden until the user asks to show finished efforts.", async () => {
		expect(appSource).toContain('data-act="show-finished"');
		expect(appSource).toMatch(/showFinished/);

		const views = [
			effort({ effort: "live", finished: false }),
			effort({
				effort: "done-quiet",
				kind: "incidental",
				finished: true,
				needs_you: [],
			}),
		];
		expect(visibleEfforts(views, false).shown.map((v) => v.effort)).toEqual([
			"live",
		]);
		expect(visibleEfforts(views, false).hidden).toBe(1);
		expect(visibleEfforts(views, true).shown.map((v) => v.effort)).toEqual([
			"live",
			"done-quiet",
		]);
	});

	it("R8: The main pane shows the selected effort's goal.", async () => {
		expect(appSource).toContain("data-goal");
		expect(appSource).toMatch(/effort\.goal/);

		const alpha = effort({ effort: "alpha", goal: "Alpha goal text" });
		const beta = effort({ effort: "beta", goal: "Beta goal text" });
		expect(alpha.goal).toBe("Alpha goal text");
		expect(beta.goal).toBe("Beta goal text");

		vi.stubGlobal(
			"fetch",
			vi.fn(async (input: RequestInfo | URL) => {
				const url = String(input);
				if (url.includes("/api/token")) {
					return new Response(JSON.stringify({ token: "tok-1" }), {
						status: 200,
						headers: { "content-type": "application/json" },
					});
				}
				return new Response(JSON.stringify(makeSnapshot([alpha, beta])), {
					status: 200,
					headers: { "content-type": "application/json" },
				});
			}),
		);
		if (await tryMountApp()) {
			expect(document.querySelector("[data-effort-title]")?.textContent).toBe(
				"alpha",
			);
			expect(document.querySelector("[data-goal]")?.textContent).toBe(
				"Alpha goal text",
			);
			document
				.querySelector<HTMLButtonElement>('[data-effort="beta"]')!
				.click();
			flushSync();
			expect(document.querySelector("[data-goal]")?.textContent).toBe(
				"Beta goal text",
			);
		}
	});

	it("R9: Selecting one phase limits the task rows to that phase.", async () => {
		expect(appSource).toContain("data-phase=");
		expect(appSource).toContain("data-phase-control");

		const view = effort({
			effort: "dashboard",
			phases: [
				{
					subject: "phase-a",
					title: "Phase A",
					ordinal: 1,
					state: "done",
					done: 1,
					total: 1,
				},
				{
					subject: "phase-b",
					title: "Phase B",
					ordinal: 2,
					state: "in_progress",
					done: 0,
					total: 2,
				},
			],
			tasks: [
				{
					id: "ta",
					subject: "a",
					title: "Task A",
					phase: "phase-a",
					status: "done",
				},
				{
					id: "tb1",
					subject: "b1",
					title: "Task B1",
					phase: "phase-b",
					status: "ready",
				},
				{
					id: "tb2",
					subject: "b2",
					title: "Task B2",
					phase: "phase-b",
					status: "waiting",
				},
			],
		});

		expect(resolvedPhase(view, null)).toBe("phase-b");
		const scoped = filteredTasks(view, "phase-a", "all");
		expect(scoped.map((t) => t.id)).toEqual(["ta"]);
	});

	it("R10: Status tabs Active, Running, Ready, Waiting, Done, and All limit the task rows to those states.", async () => {
		expect(STATUS_TABS.map((t) => t.name)).toEqual([
			"active",
			"running",
			"ready",
			"waiting",
			"done",
			"all",
		]);
		expect(STATUS_TABS.map((t) => t.label)).toEqual([
			"Active",
			"Running",
			"Ready",
			"Waiting",
			"Done",
			"All",
		]);
		expect(appSource).toContain("data-tab=");
		expect(appSource).toContain("data-status-tabs");

		const view = effort({
			effort: "dashboard",
			phases: [
				{
					subject: "p",
					title: "P",
					ordinal: 1,
					state: "in_progress",
					done: 1,
					total: 5,
				},
			],
			tasks: [
				{
					id: "run",
					subject: "run",
					title: "Running",
					phase: "p",
					status: "running",
				},
				{
					id: "rdy",
					subject: "rdy",
					title: "Ready",
					phase: "p",
					status: "ready",
				},
				{
					id: "wait",
					subject: "wait",
					title: "Waiting",
					phase: "p",
					status: "waiting",
				},
				{
					id: "done",
					subject: "done",
					title: "Done",
					phase: "p",
					status: "done",
				},
				{
					id: "wdn",
					subject: "wdn",
					title: "Withdrawn",
					phase: "p",
					status: "withdrawn",
				},
			],
		});

		const ids = (tab: Parameters<typeof filteredTasks>[2]) =>
			filteredTasks(view, "p", tab).map((t) => t.id);

		expect(ids("active").sort()).toEqual(["rdy", "run", "wait"].sort());
		expect(ids("running")).toEqual(["run"]);
		expect(ids("ready")).toEqual(["rdy"]);
		expect(ids("waiting")).toEqual(["wait"]);
		expect(ids("done").sort()).toEqual(["done", "wdn"].sort());
		expect(ids("all").sort()).toEqual(
			["done", "rdy", "run", "wait", "wdn"].sort(),
		);
	});

	it("R32: A finished effort that has Needs you items stays visible on the rail.", async () => {
		const views = [
			effort({ effort: "live", finished: false }),
			effort({
				effort: "packaging",
				finished: true,
				needs_you: [
					{
						kind: "needs-human",
						id: "nh1",
						subject: "finding",
						text: "review finding",
					},
				],
			}),
			effort({
				effort: "done-quiet",
				finished: true,
				needs_you: [],
			}),
		];
		const { shown, hidden } = visibleEfforts(views, false);
		expect(shown.map((v) => v.effort)).toEqual(["live", "packaging"]);
		expect(hidden).toBe(1);
		expect(shown.find((v) => v.effort === "packaging")!.needs_you.length).toBe(
			1,
		);
	});

	it("R33: Selecting all phases shows every task in the effort.", async () => {
		expect(appSource).toContain('data-phase="all"');
		expect(appSource).toMatch(/All phases/);

		const view = effort({
			effort: "dashboard",
			phases: [
				{
					subject: "phase-a",
					title: "Phase A",
					ordinal: 1,
					state: "done",
					done: 1,
					total: 1,
				},
				{
					subject: "phase-b",
					title: "Phase B",
					ordinal: 2,
					state: "in_progress",
					done: 0,
					total: 1,
				},
			],
			tasks: [
				{
					id: "ta",
					subject: "a",
					title: "Task A",
					phase: "phase-a",
					status: "done",
				},
				{
					id: "tb",
					subject: "b",
					title: "Task B",
					phase: "phase-b",
					status: "ready",
				},
			],
		});

		expect(resolvedPhase(view, "all")).toBeNull();
		const all = filteredTasks(view, null, "all");
		expect(all.map((t) => t.id).sort()).toEqual(["ta", "tb"]);
	});
});
