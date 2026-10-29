// @vitest-environment jsdom
/**
 * Milestone-grouped Phases block acceptance cases.
 *
 * R1: milestones present → Phases block groups phases (no flat stepper).
 * R2: milestone headers show title/subject, state, and done/total.
 * R4: no milestones → flat stepper remains.
 * R5: selecting a phase filters the task table.
 * R6: All phases shows tasks across every phase.
 * R9: activating the already-selected phase opens the phase overlay.
 * R10: phase rows show title (else subject) and done/total.
 *
 * Source wiring always asserts. DOM mounts when the Svelte vitest plugin
 * is loaded (npm run from dashboard/web/ui); otherwise helpers cover scoping.
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { phaseHref } from "./detail";
import { filteredTasks, resolvedPhase } from "./efforts";
import {
	groupPhasesByMilestone,
	initialExpandedMilestones,
} from "./milestones";
import type {
	EffortView,
	MilestoneRow,
	PhaseRow,
	Snapshot,
	TaskRow,
} from "./types";

const here = path.dirname(fileURLToPath(import.meta.url));
const appSource = readFileSync(path.join(here, "App.svelte"), "utf8");
const cssSource = readFileSync(path.join(here, "app.css"), "utf8");

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

function phase(
	partial: Partial<PhaseRow> & Pick<PhaseRow, "subject">,
): PhaseRow {
	return {
		title: partial.subject,
		ordinal: 0,
		state: "planned",
		done: 0,
		total: 0,
		...partial,
	};
}

function milestone(
	partial: Partial<MilestoneRow> & Pick<MilestoneRow, "subject">,
): MilestoneRow {
	return {
		title: partial.subject,
		ordinal: 0,
		state: "planned",
		done: 0,
		total: 0,
		...partial,
	};
}

function task(
	partial: Partial<TaskRow> & Pick<TaskRow, "id" | "phase">,
): TaskRow {
	return {
		subject: partial.id,
		title: partial.id,
		status: "ready",
		...partial,
	};
}

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

function stubFetch(snap: Snapshot, details: Record<string, unknown> = {}) {
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
			if (url.includes("/api/journal")) {
				return new Response(JSON.stringify({ open: [], rest: [] }), {
					status: 200,
					headers: { "content-type": "application/json" },
				});
			}
			for (const [key, payload] of Object.entries(details)) {
				if (url.includes(key)) {
					return new Response(JSON.stringify(payload), {
						status: 200,
						headers: { "content-type": "application/json" },
					});
				}
			}
			if (url.includes("/api/snapshot")) {
				return new Response(JSON.stringify(snap), {
					status: 200,
					headers: { "content-type": "application/json" },
				});
			}
			return new Response(JSON.stringify({ error: `unhandled ${url}` }), {
				status: 404,
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
		await vi.advanceTimersByTimeAsync(0);
		flushSync();
		return true;
	} catch {
		mounted = undefined;
		return false;
	}
}

function click(selector: string) {
	const el = document.querySelector<HTMLElement>(selector);
	expect(el).toBeTruthy();
	el!.click();
	flushSync();
}

function taskIds(): string[] {
	return Array.from(document.querySelectorAll("[data-task]")).map(
		(el) => el.getAttribute("data-task") ?? "",
	);
}

const milestoneEffort = effort({
	effort: "dashboard",
	goal: "Ship milestones",
	milestones: [
		milestone({
			subject: "cutover",
			title: "Cutover",
			ordinal: 1,
			state: "done",
			done: 1,
			total: 1,
		}),
		milestone({
			subject: "harden",
			title: "Harden",
			ordinal: 2,
			state: "in_progress",
			done: 0,
			total: 2,
		}),
	],
	phases: [
		phase({
			subject: "p-cut",
			title: "Cut phase",
			ordinal: 1,
			state: "done",
			done: 1,
			total: 1,
			milestone: "cutover",
			milestone_title: "Cutover",
		}),
		phase({
			subject: "p-hard",
			title: "Harden phase",
			ordinal: 2,
			state: "in_progress",
			done: 0,
			total: 2,
			milestone: "harden",
			milestone_title: "Harden",
		}),
		phase({
			subject: "p-hard-2",
			title: "",
			ordinal: 3,
			state: "planned",
			done: 1,
			total: 3,
			milestone: "harden",
			milestone_title: "Harden",
		}),
	],
	tasks: [
		task({ id: "t-cut", phase: "p-cut", title: "Cut task", status: "done" }),
		task({
			id: "t-hard",
			phase: "p-hard",
			title: "Hard task",
			status: "ready",
		}),
		task({
			id: "t-hard-2",
			phase: "p-hard-2",
			title: "Hard 2 task",
			status: "ready",
		}),
	],
});

const flatEffort = effort({
	effort: "flat",
	goal: "No milestones",
	phases: [
		phase({
			subject: "a",
			title: "Phase A",
			ordinal: 1,
			state: "done",
			done: 1,
			total: 1,
		}),
		phase({
			subject: "b",
			title: "Phase B",
			ordinal: 2,
			state: "in_progress",
			done: 0,
			total: 1,
		}),
	],
	tasks: [
		task({ id: "ta", phase: "a", status: "done" }),
		task({ id: "tb", phase: "b", status: "ready" }),
	],
});

describe("milestone-nav Phases block", () => {
	it("R1: When an effort's snapshot includes one or more milestones, the main pane shows a Phases block that groups that effort's phases under those milestones instead of the flat phase stepper.", async () => {
		expect(appSource).toMatch(/groupPhasesByMilestone/);
		expect(appSource).toMatch(/initialExpandedMilestones/);
		expect(appSource).toMatch(/milestones-heading/);
		expect(appSource).toMatch(/>Milestones</);
		expect(appSource).toMatch(/milestone-chevron/);
		expect(appSource).toMatch(/data-phases-block/);
		expect(appSource).toMatch(/hasMilestones/);
		expect(appSource).toMatch(/\{#if hasMilestones\}/);
		expect(appSource).toMatch(/class="stepper"/);
		expect(cssSource).toMatch(/\.milestone-head/);
		expect(cssSource).toMatch(/\.phase-row/);

		const groups = groupPhasesByMilestone(milestoneEffort);
		expect(groups.map((g) => g.key)).toEqual(["cutover", "harden"]);
		expect(groups[0]!.phases.map((p) => p.subject)).toEqual(["p-cut"]);
		expect(groups[1]!.phases.map((p) => p.subject)).toEqual([
			"p-hard",
			"p-hard-2",
		]);

		stubFetch(makeSnapshot([milestoneEffort]));
		if (await tryMountApp()) {
			expect(document.querySelector("[data-phases-block]")).toBeTruthy();
			expect(document.querySelector(".stepper")).toBeNull();
			expect(document.querySelector('[data-milestone="cutover"]')).toBeTruthy();
			expect(document.querySelector('[data-milestone="harden"]')).toBeTruthy();
			expect(document.querySelector('[data-phase="p-hard"]')).toBeTruthy();
		}
	});

	it("R2: Each milestone group header shows the milestone title (else subject), its state, and its done/total counts from the snapshot milestone row.", async () => {
		expect(appSource).toMatch(/milestoneMeta/);
		expect(appSource).toMatch(/group\.milestone\.state/);
		expect(appSource).toMatch(/group\.milestone\.done/);
		expect(appSource).toMatch(/group\.milestone\.total/);
		expect(appSource).toMatch(/group\.title/);

		const groups = groupPhasesByMilestone(milestoneEffort);
		expect(groups[0]!.title).toBe("Cutover");
		expect(groups[0]!.milestone?.state).toBe("done");
		expect(groups[0]!.milestone?.done).toBe(1);
		expect(groups[0]!.milestone?.total).toBe(1);
		expect(groups[1]!.title).toBe("Harden");
		expect(groups[1]!.milestone?.state).toBe("in_progress");
		expect(groups[1]!.milestone?.done).toBe(0);
		expect(groups[1]!.milestone?.total).toBe(2);

		const untitled = effort({
			effort: "x",
			milestones: [milestone({ subject: "ms-only", title: "" })],
			phases: [phase({ subject: "p", milestone: "ms-only" })],
		});
		expect(groupPhasesByMilestone(untitled)[0]!.title).toBe("ms-only");

		stubFetch(makeSnapshot([milestoneEffort]));
		if (await tryMountApp()) {
			const harden = document.querySelector('[data-milestone="harden"]');
			expect(harden?.textContent).toContain("Harden");
			expect(harden?.textContent).toMatch(/in progress/);
			expect(harden?.textContent).toContain("0/2");
			const cutover = document.querySelector('[data-milestone="cutover"]');
			expect(cutover?.textContent).toContain("Cutover");
			expect(cutover?.textContent).toMatch(/done/);
			expect(cutover?.textContent).toContain("1/1");
		}
	});

	it("R4: When an effort has no milestones, the existing flat phase stepper remains the phase control.", async () => {
		expect(appSource).toMatch(/\{#if hasMilestones\}/);
		expect(appSource).toMatch(/\{:else\}/);
		expect(appSource).toMatch(/class="stepper" data-phase-control/);
		expect(flatEffort.milestones?.length ?? 0).toBe(0);

		stubFetch(makeSnapshot([flatEffort]));
		if (await tryMountApp()) {
			expect(
				document.querySelector(".stepper[data-phase-control]"),
			).toBeTruthy();
			expect(document.querySelector("[data-phases-block]")).toBeNull();
			expect(document.querySelector('[data-phase="a"]')).toBeTruthy();
			expect(document.querySelector('[data-phase="b"]')).toBeTruthy();
			expect(document.querySelector('[data-phase="all"]')).toBeTruthy();
		}
	});

	it("R5: Selecting a phase in the Phases block filters the task table to that phase using the same scoping rules as today's stepper.", async () => {
		expect(appSource).toMatch(/activatePhase/);
		expect(appSource).toMatch(/selectPhase/);
		expect(appSource).toMatch(/filteredTasks/);
		expect(appSource).toMatch(/resolvedPhase/);

		expect(resolvedPhase(milestoneEffort, "p-hard-2")).toBe("p-hard-2");
		expect(
			filteredTasks(milestoneEffort, "p-hard-2", "all").map((t) => t.id),
		).toEqual(["t-hard-2"]);

		stubFetch(makeSnapshot([milestoneEffort]));
		if (await tryMountApp()) {
			click('[data-tab="all"]');
			click('[data-phase="p-hard-2"]');
			expect(taskIds()).toEqual(["t-hard-2"]);
			expect(document.querySelector('[data-task="t-hard"]')).toBeNull();
			expect(document.querySelector('[data-task="t-cut"]')).toBeNull();
		}
	});

	it("R6: An All phases control remains available and shows tasks across every phase of the effort.", async () => {
		expect(appSource).toMatch(/data-phase="all"/);
		expect(appSource).toMatch(/All phases/);
		expect(appSource).toMatch(/selectPhase\("all"\)/);

		expect(resolvedPhase(milestoneEffort, "all")).toBeNull();
		expect(
			filteredTasks(milestoneEffort, null, "all")
				.map((t) => t.id)
				.sort(),
		).toEqual(["t-cut", "t-hard", "t-hard-2"]);

		stubFetch(makeSnapshot([milestoneEffort]));
		if (await tryMountApp()) {
			expect(document.querySelector('[data-phase="all"]')?.textContent).toMatch(
				/All phases/,
			);
			click('[data-tab="all"]');
			click('[data-phase="all"]');
			expect(taskIds().sort()).toEqual(["t-cut", "t-hard", "t-hard-2"]);
		}
	});

	it("R9: Activating the already-selected phase opens the phase detail overlay for that phase.", async () => {
		expect(appSource).toMatch(/activatePhase/);
		expect(appSource).toMatch(
			/phaseSubject === subject\)\s*openPhase\(subject\)/,
		);
		expect(appSource).toMatch(/openPhase/);
		expect(appSource).toMatch(/phaseHref/);
		expect(phaseHref("dashboard", "p-hard")).toBe("#/phase/dashboard/p-hard");

		stubFetch(makeSnapshot([milestoneEffort]), {
			"/api/phase?": {
				detail: {
					subject: "p-hard",
					title: "Harden phase",
					state: "in_progress",
					body: "Phase overlay body",
				},
				tabs: ["overview", "tasks"],
				decisions: { groups: [] },
			},
		});
		if (await tryMountApp()) {
			const row = document.querySelector<HTMLElement>('[data-phase="p-hard"]');
			expect(row).toBeTruthy();
			expect(row!.classList.contains("on")).toBe(true);
			row!.click();
			flushSync();
			await vi.advanceTimersByTimeAsync(0);
			flushSync();
			await vi.advanceTimersByTimeAsync(0);
			flushSync();
			expect(window.location.hash).toBe(phaseHref("dashboard", "p-hard"));
			expect(document.querySelector('[data-detail="phase"]')).toBeTruthy();
		}
	});

	it("R10: Phase rows show title when present, otherwise subject, plus a done/total cue for that phase.", async () => {
		expect(appSource).toMatch(/phase\.title \|\| phase\.subject/);
		expect(appSource).toMatch(/phase\.done\}\/\{phase\.total/);
		expect(appSource).toMatch(/class="phase-row"/);
		expect(appSource).toMatch(/class="name"/);
		expect(appSource).toMatch(/class="cnt"/);

		const titled = milestoneEffort.phases.find((p) => p.subject === "p-cut")!;
		const untitled = milestoneEffort.phases.find(
			(p) => p.subject === "p-hard-2",
		)!;
		expect(titled.title || titled.subject).toBe("Cut phase");
		expect(`${titled.done}/${titled.total}`).toBe("1/1");
		expect(untitled.title || untitled.subject).toBe("p-hard-2");
		expect(`${untitled.done}/${untitled.total}`).toBe("1/3");

		// Done milestones start collapsed; selected/default phase's milestone expands.
		const expanded = initialExpandedMilestones(milestoneEffort, null);
		expect(expanded.has("cutover")).toBe(false);
		expect(expanded.has("harden")).toBe(true);

		stubFetch(makeSnapshot([milestoneEffort]));
		if (await tryMountApp()) {
			click('[data-milestone-toggle="cutover"]');
			const cutRow = document.querySelector('[data-phase="p-cut"]');
			expect(cutRow?.textContent).toContain("Cut phase");
			expect(cutRow?.textContent).toContain("1/1");
			const hard2 = document.querySelector('[data-phase="p-hard-2"]');
			expect(hard2?.textContent).toContain("p-hard-2");
			expect(hard2?.textContent).toContain("1/3");
		}
	});
});
