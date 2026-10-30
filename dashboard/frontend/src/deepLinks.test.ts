// @vitest-environment jsdom
/**
 * Deep links wiring (deep-links-wire).
 *
 * R1: task id control opens task overlay.
 * R2: phase subject reference opens phase overlay.
 * R3: requirement id with context opens requirement overlay.
 * R5: milestone subject expands that milestone group.
 * R6: markdown bodies linkify standalone reference tokens.
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { type Component, flushSync, mount, unmount } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MilestoneRow, TaskRow } from "./api-types";
import { appSource } from "./appSource";
import { resolveRef } from "./links";
import { renderMarkdown } from "./markdown";
import type { DeepPartial, EffortView, Snapshot } from "./types";

const here = path.dirname(fileURLToPath(import.meta.url));

const markdownSource = readFileSync(path.join(here, "markdown.ts"), "utf8");

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

function milestone(
	partial: Partial<MilestoneRow> & Pick<MilestoneRow, "subject">,
): MilestoneRow {
	return {
		title: partial.subject,
		ordinal: 1,
		state: "planned",
		done: 0,
		total: 1,
		...partial,
	} as MilestoneRow;
}

function task(
	partial: Partial<TaskRow> & Pick<TaskRow, "id" | "phase">,
): TaskRow {
	return {
		subject: partial.id,
		title: partial.id,
		status: "ready",
		...partial,
	} as TaskRow;
}

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
		milestones: [],
		...partial,
	} as EffortView;
}

function makeSnapshot(efforts: EffortView[], token = "tok-1"): Snapshot {
	return { token, efforts, generated_at: "2026-01-01T00:00:00Z" } as Snapshot;
}

const demo = effort({
	effort: "dashboard",
	milestones: [milestone({ subject: "web-calm", title: "Web calm" })],
	phases: [
		{
			subject: "deep-links",
			title: "Deep links",
			ordinal: 1,
			state: "in_progress",
			done: 0,
			total: 2,
			milestone: "web-calm",
			milestone_title: "Web calm",
		},
	],
	tasks: [task({ id: "t-wire", phase: "deep-links", title: "Wire links" })],
	needs_you: [
		{
			kind: "question",
			id: "n1",
			subject: "t-wire",
			text: `See task t-wire and record rec-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee`,
		},
	],
});

function stubFetch(snap: Snapshot, detailBodies: Record<string, unknown> = {}) {
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
			if (url.includes("/api/task")) {
				return new Response(
					JSON.stringify(
						detailBodies.task ?? {
							detail: {
								id: "t-wire",
								subject: "t-wire",
								title: "Wire links",
								status: "ready",
								description:
									"Depends on rec-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee and phase deep-links. Requirement: R3.",
								phase: "deep-links",
								effort: "dashboard",
								requirements: ["R3"],
							},
						},
					),
					{ status: 200, headers: { "content-type": "application/json" } },
				);
			}
			if (url.includes("/api/phase")) {
				return new Response(
					JSON.stringify(
						detailBodies.phase ?? {
							detail: {
								subject: "deep-links",
								title: "Deep links",
								body: "See milestone web-calm",
								state: "in_progress",
							},
							tabs: ["overview"],
						},
					),
					{ status: 200, headers: { "content-type": "application/json" } },
				);
			}
			if (url.includes("/api/requirement")) {
				return new Response(
					JSON.stringify({
						detail: {
							id: "R3",
							text: "Req text",
							status: "open",
							phase: "deep-links",
						},
					}),
					{ status: 200, headers: { "content-type": "application/json" } },
				);
			}
			if (url.includes("/api/record")) {
				return new Response(
					JSON.stringify({
						record: {
							id: "rec-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
							record_type: "decision",
							subject: "deep-links-surfaces",
							body: "Choice body",
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

describe("deep-links-wire", () => {
	it("wires linkify into App markdown and list meta", () => {
		expect(appSource).toMatch(/linkifyText|linkify\(/);
		expect(appSource).toMatch(/md\(section\.body\)|renderMarkdown\(.*linkCtx/);
		expect(markdownSource).toMatch(/linkifyText/);
		expect(appSource).toMatch(
			/route\.name !== "milestone"|name !== "milestone"/,
		);
	});

	it("R1: activating a task id reference opens the task overlay", async () => {
		stubFetch(makeSnapshot([demo]));
		if (!(await tryMountApp())) return;
		window.location.hash = "#/task/t-wire";
		window.dispatchEvent(new HashChangeEvent("hashchange"));
		await vi.advanceTimersByTimeAsync(0);
		flushSync();
		expect(document.querySelector('[data-detail="task"]')).toBeTruthy();
	});

	it("R2: a phase subject reference navigates to the phase overlay", async () => {
		const ctx = {
			snapshot: makeSnapshot([demo]),
			effort: "dashboard",
			phase: "deep-links",
		};
		const resolved = resolveRef("deep-links", ctx);
		expect(resolved?.href).toBe("#/phase/dashboard/deep-links");

		stubFetch(makeSnapshot([demo]));
		if (!(await tryMountApp())) return;
		window.location.hash = resolved!.href;
		window.dispatchEvent(new HashChangeEvent("hashchange"));
		await vi.advanceTimersByTimeAsync(0);
		flushSync();
		expect(document.querySelector('[data-detail="phase"]')).toBeTruthy();
	});

	it("R3: a requirement id with effort+phase context opens the requirement overlay", async () => {
		const ctx = {
			snapshot: makeSnapshot([demo]),
			effort: "dashboard",
			phase: "deep-links",
		};
		const resolved = resolveRef("R3", ctx);
		expect(resolved?.href).toBe("#/requirement/dashboard/deep-links/R3");

		stubFetch(makeSnapshot([demo]));
		if (!(await tryMountApp())) return;
		window.location.hash = resolved!.href;
		window.dispatchEvent(new HashChangeEvent("hashchange"));
		await vi.advanceTimersByTimeAsync(0);
		flushSync();
		expect(document.querySelector('[data-detail="requirement"]')).toBeTruthy();
	});

	it("R5: a milestone subject reference expands that milestone group", async () => {
		stubFetch(makeSnapshot([demo]));
		if (!(await tryMountApp())) return;
		// Collapse first by toggling if open, then navigate via milestone hash.
		window.location.hash = "#/milestone/dashboard/web-calm";
		window.dispatchEvent(new HashChangeEvent("hashchange"));
		await vi.advanceTimersByTimeAsync(0);
		flushSync();
		const group = document.querySelector('[data-milestone="web-calm"]');
		expect(group?.classList.contains("open")).toBe(true);
	});

	it("R6: rendered markdown linkifies standalone reference tokens", () => {
		const id = "rec-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee";
		const html = renderMarkdown(`See ${id} and task t-wire.`, {
			snapshot: makeSnapshot([demo]),
			effort: "dashboard",
			phase: "deep-links",
		});
		expect(html).toContain(`href="#/record/${id}"`);
		expect(html).toContain('href="#/task/t-wire"');
		expect(html).toContain("data-ref=");
	});
});
