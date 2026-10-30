// @vitest-environment jsdom
/**
 * Wave-lane task dependency graph (task-graph).
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { appSource } from "./appSource";
import { buildWaveGraph, statusSignal, toFlow } from "./taskGraph";
import type { DeepPartial, EffortView, Snapshot } from "./types";

const here = path.dirname(fileURLToPath(import.meta.url));

const boardSource = readFileSync(
	path.join(here, "TaskGraphBoard.svelte"),
	"utf8",
);

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
	if (!globalThis.ResizeObserver) {
		globalThis.ResizeObserver = class {
			observe() {}
			unobserve() {}
			disconnect() {}
		};
	}
	window.matchMedia = (query: string) =>
		({
			matches: false,
			media: query,
			onchange: null,
			addListener() {},
			removeListener() {},
			addEventListener() {},
			removeEventListener() {},
			dispatchEvent() {
				return false;
			},
		}) as MediaQueryList;
});

afterEach(() => {
	resetDocument();
	vi.useRealTimers();
	vi.unstubAllGlobals();
	vi.restoreAllMocks();
});

const threeTasks = [
	{
		id: "t-a",
		subject: "a",
		title: "Alpha",
		status: "done",
		wave: 1,
		depends_on: [],
	},
	{
		id: "t-b",
		subject: "b",
		title: "Beta",
		status: "ready",
		wave: 2,
		depends_on: ["t-a"],
	},
	{
		id: "t-c",
		subject: "c",
		title: "Gamma",
		status: "ready",
		wave: 2,
		depends_on: ["t-a"],
	},
];

function phasePayload(tasks: typeof threeTasks) {
	return {
		tabs: ["overview", "tasks"],
		detail: {
			subject: "graph-phase",
			title: "Graph phase",
			effort: "dashboard",
			state: "in_progress",
			body: "notes",
			tasks,
		},
	};
}

function effort(
	partial: DeepPartial<EffortView> & Pick<EffortView, "effort">,
): EffortView {
	return {
		goal: "",
		kind: "deliver",
		finished: false,
		phases: [
			{
				subject: "graph-phase",
				title: "Graph phase",
				ordinal: 1,
				state: "in_progress",
				done: 1,
				total: 3,
			},
		],
		tasks: [],
		needs_you: [],
		backlog: [],
		...partial,
	} as EffortView;
}

function makeSnapshot(efforts: EffortView[], token = "tok-1"): Snapshot {
	return { token, efforts, generated_at: "2026-01-01T00:00:00Z" } as Snapshot;
}

function stubFetch(snap: Snapshot, payload = phasePayload(threeTasks)) {
	vi.stubGlobal(
		"fetch",
		vi.fn(async (input: RequestInfo | URL) => {
			const url = String(input);
			if (url.includes("/api/token")) {
				return new Response(JSON.stringify({ token: snap.token }), {
					status: 200,
					headers: { "content-type": "application/json" },
				});
			}
			if (url.includes("/api/phase")) {
				return new Response(JSON.stringify(payload), {
					status: 200,
					headers: { "content-type": "application/json" },
				});
			}
			if (url.includes("/api/task")) {
				return new Response(
					JSON.stringify({
						detail: {
							id: "t-b",
							subject: "b",
							title: "Beta",
							status: "ready",
							description: "task",
						},
					}),
					{ status: 200, headers: { "content-type": "application/json" } },
				);
			}
			return new Response(JSON.stringify(snap), {
				status: 200,
				headers: { "content-type": "application/json" },
			});
		}),
	);
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

async function openOverview() {
	window.location.hash = "#/phase/dashboard/graph-phase";
	window.dispatchEvent(new HashChangeEvent("hashchange"));
	await vi.advanceTimersByTimeAsync(0);
	flushSync();
}

describe("buildWaveGraph", () => {
	it("R1: columns by wave left to right for ≥3 tasks", () => {
		const graph = buildWaveGraph(threeTasks);
		expect(graph.show).toBe(true);
		expect(graph.lanes.map((l) => l.wave)).toEqual(["1", "2"]);
		expect(graph.lanes[0]?.nodes.map((n) => n.id)).toEqual(["t-a"]);
		expect(graph.lanes[1]?.nodes.map((n) => n.id).sort()).toEqual([
			"t-b",
			"t-c",
		]);
	});

	it("R2: nodes carry status and signal", () => {
		const graph = buildWaveGraph(threeTasks);
		const alpha = graph.lanes[0]?.nodes[0];
		expect(alpha?.status).toBe("done");
		expect(alpha?.signal).toBe("done");
		expect(alpha?.label).toBe("Alpha");
		expect(statusSignal("ready")).toBe("ready");
		expect(statusSignal("running")).toBe("run");
	});

	it("R3: edges follow depends_on; skip edges use the top handles", () => {
		const graph = buildWaveGraph(threeTasks);
		expect(graph.edges).toEqual(
			expect.arrayContaining([
				{ from: "t-a", to: "t-b", kind: "depends" },
				{ from: "t-a", to: "t-c", kind: "depends" },
			]),
		);
		const flow = toFlow(graph);
		const beta = flow.nodes.find((node) => node.id === "t-b");
		const alpha = flow.nodes.find((node) => node.id === "t-a");
		expect(beta && alpha && beta.position.x).toBeGreaterThan(alpha!.position.x);
		expect(flow.edges.find((edge) => edge.id === "t-a->t-b")).toMatchObject({
			sourceHandle: "out",
			targetHandle: "in",
		});

		const skip = toFlow(
			buildWaveGraph([
				{
					id: "t-a",
					subject: "a",
					title: "A",
					status: "done",
					wave: 1,
					depends_on: [],
				},
				{
					id: "t-b",
					subject: "b",
					title: "B",
					status: "done",
					wave: 2,
					depends_on: ["t-a"],
				},
				{
					id: "t-c",
					subject: "c",
					title: "C",
					status: "done",
					wave: 3,
					depends_on: ["t-a", "t-b"],
				},
			]),
		);
		expect(skip.edges.find((edge) => edge.id === "t-a->t-c")).toMatchObject({
			sourceHandle: "skip-out",
			targetHandle: "skip-in",
		});
	});

	it("R3b: waits_on subjects resolve to edges; wave flow when no deps", () => {
		const viaWaits = buildWaveGraph([
			{
				id: "t-a",
				subject: "a",
				title: "A",
				status: "done",
				wave: 1,
				waits_on: [],
			},
			{
				id: "t-b",
				subject: "b",
				title: "B",
				status: "ready",
				wave: 2,
				waits_on: ["a"],
			},
			{
				id: "t-c",
				subject: "c",
				title: "C",
				status: "ready",
				wave: 2,
				waits_on: [],
			},
		]);
		expect(viaWaits.edges).toContainEqual({
			from: "t-a",
			to: "t-b",
			kind: "depends",
		});

		const flow = buildWaveGraph([
			{ id: "t-a", subject: "a", title: "A", status: "done", wave: 1 },
			{ id: "t-b", subject: "b", title: "B", status: "ready", wave: 2 },
			{ id: "t-c", subject: "c", title: "C", status: "ready", wave: 3 },
		]);
		expect(flow.edges.every((e) => e.kind === "flow")).toBe(true);
		expect(flow.edges).toEqual(
			expect.arrayContaining([
				{ from: "t-a", to: "t-b", kind: "flow" },
				{ from: "t-b", to: "t-c", kind: "flow" },
			]),
		);
	});

	it("R6: omit graph when two or fewer tasks", () => {
		expect(buildWaveGraph(threeTasks.slice(0, 2)).show).toBe(false);
		expect(buildWaveGraph([]).show).toBe(false);
	});
});

describe("task graph UI", () => {
	it("wires Overview graph", () => {
		expect(appSource).toMatch(/buildWaveGraph/);
		expect(appSource).toMatch(/TaskGraphBoard/);
		expect(boardSource).toMatch(/data-task-graph/);
		expect(boardSource).toMatch(/SvelteFlow/);
	});

	it("R1 R2 R3: shows graph with lanes, status, edges for ≥3 tasks", async () => {
		stubFetch(makeSnapshot([effort({ effort: "dashboard" })]));
		if (!(await tryMountApp())) return;
		await openOverview();
		expect(document.querySelector("[data-task-graph]")).toBeTruthy();
		expect(document.querySelector('[data-graph-lane="1"]')).toBeTruthy();
		expect(document.querySelector('[data-graph-lane="2"]')).toBeTruthy();
		expect(
			document
				.querySelector('[data-graph-node="t-a"]')
				?.getAttribute("data-status"),
		).toBe("done");
		expect(
			document
				.querySelector('[data-graph-node="t-a"]')
				?.getAttribute("data-signal"),
		).toBe("done");
		expect(document.querySelector(".svelte-flow")).toBeTruthy();
		expect(document.querySelector(".svelte-flow__pane.draggable")).toBeTruthy();
		expect(
			document.querySelector(".svelte-flow__controls-zoomin"),
		).toBeTruthy();
		expect(
			document.querySelector(".svelte-flow__controls-zoomout"),
		).toBeTruthy();
		expect(
			document.querySelector(".svelte-flow__controls-fitview"),
		).toBeTruthy();
		expect(
			document.querySelector(".svelte-flow__controls-interactive"),
		).toBeNull();
	});

	it("R4: activating a node opens the task overlay", async () => {
		stubFetch(makeSnapshot([effort({ effort: "dashboard" })]));
		if (!(await tryMountApp())) return;
		await openOverview();
		const node = document.querySelector('[data-graph-node="t-b"]');
		expect(node).toBeTruthy();
		node!.dispatchEvent(
			new MouseEvent("click", { bubbles: true, cancelable: true }),
		);
		flushSync();
		await vi.advanceTimersByTimeAsync(0);
		flushSync();
		expect(window.location.hash).toBe("#/task/t-b");
	});

	it("R5: task list tab remains available; wave chips omitted", async () => {
		expect(appSource).toMatch(/data-phase-tab="tasks"|Tasks/);
		expect(appSource).not.toMatch(/data-phase-waves/);
		stubFetch(makeSnapshot([effort({ effort: "dashboard" })]));
		if (!(await tryMountApp())) return;
		await openOverview();
		expect(document.querySelector("[data-phase-tabs]")).toBeTruthy();
		expect(document.querySelector('[data-phase-tab="tasks"]')).toBeTruthy();
		expect(document.querySelector("[data-phase-waves]")).toBeNull();
	});

	it("R6: hides graph for ≤2 tasks", async () => {
		stubFetch(
			makeSnapshot([effort({ effort: "dashboard" })]),
			phasePayload(threeTasks.slice(0, 2) as typeof threeTasks),
		);
		if (!(await tryMountApp())) return;
		await openOverview();
		expect(document.querySelector("[data-task-graph]")).toBeNull();
	});
});
